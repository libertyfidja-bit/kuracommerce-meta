"""Meta Model API client for KuraCommerce Hub.

Four models are used, one per pipeline step:

    sam         SAM 3.1      segment the product from its background
    wonder      Muse Wonder  read the photo -> title, category, description, RWF price
    image       Muse Image   studio-style enhancement of the product photo
    spark       Muse Spark   Kinyarwanda / English / French promotional copy

Every public function returns ``(result, step_meta)``. ``step_meta`` records which
model ran, whether the real Meta API answered or the local fallback did, how long it
took, and why a fallback was used. The UI and /api/status show this, so a broken or
missing API key can never pass as working AI.

NOTE: endpoint paths and response shapes below follow the request format used in the
original project. Check them against the current Meta Model API docs and adjust
``_post`` calls if they differ. Base URL and model IDs can be overridden via env vars.
"""
import base64
import io
import json
import logging
import os
import re
import time

import requests

log = logging.getLogger("kuracommerce.meta")

META_API_BASE = os.getenv("META_API_BASE", "https://api.dev.meta.ai/v1").rstrip("/")
MODELS = {
    "sam": os.getenv("META_MODEL_SAM", "sam-3.1"),
    "wonder": os.getenv("META_MODEL_WONDER", "muse-wonder"),
    "image": os.getenv("META_MODEL_IMAGE", "muse-image"),
    "spark": os.getenv("META_MODEL_SPARK", "muse-spark"),
}
PLACEHOLDER_KEY = "your_meta_api_key_here"

# Which steps call a live model. Default: all four. When you self-host one open-weight model
# (for example Muse Glimmer) that only does chat + vision, set LIVE_STEPS=wonder,spark so the
# SAM and image steps use the local fallback instead of failing against a server that lacks them.
LIVE_STEPS = {x.strip() for x in os.getenv("LIVE_STEPS", "sam,wonder,image,spark").split(",") if x.strip()}
# Self-hosted models on free GPUs are slower; scale all request timeouts (for example 3).
TIMEOUT_SCALE = float(os.getenv("TIMEOUT_SCALE", "1"))
PROVIDER_LABEL = os.getenv("MODEL_PROVIDER_LABEL", "Meta Model API")


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
# Runtime override so a changing tunnel URL (Kaggle/Colab) can be set without redeploying.
_endpoint = {"base": META_API_BASE, "key": None}


def set_endpoint(base: str, key: str = None):
    _endpoint["base"] = base.rstrip("/")
    if key:
        _endpoint["key"] = key.strip()


def current_base() -> str:
    return _endpoint["base"]


def _api_key() -> str:
    # Read at call time, not import time, so .env loaded after import still works.
    return _endpoint["key"] or os.getenv("META_API_KEY", "").strip()


def api_configured() -> bool:
    key = _api_key()
    return bool(key) and key != PLACEHOLDER_KEY


def _post(path: str, payload: dict, timeout: int) -> dict:
    res = requests.post(
        f"{_endpoint['base']}{path}",
        headers={"Authorization": f"Bearer {_api_key()}", "Content-Type": "application/json"},
        json=payload,
        timeout=timeout * TIMEOUT_SCALE,
    )
    res.raise_for_status()
    return res.json()


def _loads_lenient(text: str) -> dict:
    """Parse JSON from a model reply, tolerating ```json fences and stray prose."""
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE)
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object in model reply")
    return json.loads(text[start:end + 1])


def _chat_json(model: str, messages: list, timeout: int) -> dict:
    data = _post(
        "/chat/completions",
        {"model": model, "messages": messages, "response_format": {"type": "json_object"}},
        timeout,
    )
    return _loads_lenient(data["choices"][0]["message"]["content"])


def _detect_mime(image_b64: str) -> str:
    try:
        head = base64.b64decode(image_b64[:48] + "=" * (-len(image_b64[:48]) % 4))
    except Exception:
        return "image/jpeg"
    if head.startswith(b"\x89PNG"):
        return "image/png"
    if head.startswith(b"RIFF"):
        return "image/webp"
    return "image/jpeg"


def _run_step(key: str, live_fn, fallback_fn):
    """Try the live Meta call; on any problem use the fallback and say so."""
    t0 = time.time()
    result, source, error = None, "fallback", None
    if key not in LIVE_STEPS:
        error = "step not enabled in LIVE_STEPS"
    elif api_configured():
        try:
            result, source = live_fn(), "meta_api"
        except Exception as exc:  # network, HTTP, parsing, validation
            error = f"{type(exc).__name__}: {exc}"[:200]
            log.warning("Meta %s call failed, using fallback: %s", key, error)
    else:
        error = "META_API_KEY not configured"
    if result is None:
        result = fallback_fn()
    meta = {
        "step": key,
        "model": MODELS[key],
        "source": source,
        "provider": PROVIDER_LABEL,
        "fallback": source == "fallback",
        "ms": int((time.time() - t0) * 1000),
        "error": error,
    }
    return result, meta


# --------------------------------------------------------------------------- #
# Local fallback: honest, simple image inspection (Pillow)
# --------------------------------------------------------------------------- #
CATEGORY_RULES = [
    (("barber", "salon", "hair", "cut", "shave"), "Barber & Grooming Service", "5,000"),
    (("market", "food", "fruit", "veg", "fresh", "produce"), "Local Market & Fresh Produce", "3,500"),
    (("tailor", "shirt", "dress", "fashion", "shoe", "cloth", "kitenge"), "Fashion & Tailoring", "15,000"),
    (("electronics", "phone", "laptop", "repair"), "Electronics & Repair Service", "25,000"),
]


def _inspect_uploaded_image(image_b64: str, filename: str = "", category_hint: str = "") -> dict:
    """Fallback only: average colour/brightness + keyword price guess. Not AI."""
    clean = os.path.splitext(filename)[0].replace("_", " ").replace("-", " ").strip().title()
    width = height = 0
    tone, colour = "balanced natural lighting", "natural textured tones"
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(base64.b64decode(image_b64))).convert("RGB")
        width, height = img.size
        r, g, b = img.resize((1, 1)).getpixel((0, 0))
        brightness = (r + g + b) / 3
        tone = ("bright, well-lit" if brightness > 150
                else "high-contrast" if brightness > 85 else "dark, heavily shaded")
        if r > g + 25 and r > b + 25:
            colour = "warm red and amber hues"
        elif g > r + 20 and g > b + 20:
            colour = "green, fresh tones"
        elif b > r + 20 and b > g + 20:
            colour = "cool blue tones"
    except Exception:
        pass

    subject = clean if clean and clean.lower() not in {"image", "photo", "download", "test"} \
        else (category_hint or "Featured Local Item")
    haystack = f"{category_hint} {subject}".lower()
    label, price = category_hint or "General Commerce & Crafts", "12,000"
    for words, cat_label, cat_price in CATEGORY_RULES:
        if any(w in haystack for w in words):
            label, price = cat_label, cat_price
            break
    size = f" ({width}x{height}px)" if width else ""
    return {
        "title": subject,
        "category": label,
        "estimated_price_rwf": price,
        "description": f"Photo of {subject}{size}: {tone}, dominant {colour}. "
                       "(Basic local analysis; the Muse Wonder model was not used.)",
    }


def _local_studio_enhance(image_b64: str) -> dict:
    """Fallback only: auto-contrast + light sharpening so the 'studio' panel is real."""
    try:
        from PIL import Image, ImageEnhance, ImageOps
        img = Image.open(io.BytesIO(base64.b64decode(image_b64))).convert("RGB")
        img = ImageOps.autocontrast(img, cutoff=1)
        img = ImageEnhance.Color(img).enhance(1.15)
        img = ImageEnhance.Sharpness(img).enhance(1.4)
        img = ImageEnhance.Brightness(img).enhance(1.05)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=88)
        return {"enhanced_image_b64": base64.b64encode(buf.getvalue()).decode(), "mime": "image/jpeg"}
    except Exception:
        return {"enhanced_image_b64": image_b64, "mime": _detect_mime(image_b64)}


# --------------------------------------------------------------------------- #
# Step 1: SAM 3.1
# --------------------------------------------------------------------------- #
def segment_product_with_sam(image_b64: str):
    def live():
        return _post("/vision/segment",
                     {"model": MODELS["sam"], "image": image_b64, "mode": "automatic"}, 20)

    def fallback():
        return {"mask_isolated": False, "note": "no segmentation performed locally"}

    return _run_step("sam", live, fallback)


# --------------------------------------------------------------------------- #
# Step 2: Muse Wonder
# --------------------------------------------------------------------------- #
def _normalize_catalog(raw: dict, filename: str, category_hint: str) -> dict:
    base = _inspect_uploaded_image("", filename, category_hint)  # defaults only
    title = str(raw.get("title") or base["title"]).strip()[:120]
    digits = re.sub(r"[^\d]", "", str(raw.get("estimated_price_rwf", "")))
    price = f"{int(digits):,}" if digits else base["estimated_price_rwf"]
    return {
        "title": title or "Featured Item",
        "category": str(raw.get("category") or base["category"]).strip()[:80],
        "description": str(raw.get("description") or "").strip()[:600] or base["description"],
        "estimated_price_rwf": price,
    }


def analyze_product_with_muse_wonder(image_b64: str, filename: str = "", category_hint: str = ""):
    def live():
        mime = _detect_mime(image_b64)
        raw = _chat_json(
            MODELS["wonder"],
            [
                {"role": "system", "content": (
                    "You catalogue products for small merchants in Rwanda. Inspect the image and "
                    "return strict JSON with keys 'title', 'category', 'description' (2 sentences, "
                    "what is visibly shown) and 'estimated_price_rwf' (integer, fair local price "
                    "in Rwandan francs).")},
                {"role": "user", "content": [
                    {"type": "text", "text": f"Merchant hint: {filename} / {category_hint}"},
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{image_b64}"}},
                ]},
            ],
            25,
        )
        return _normalize_catalog(raw, filename, category_hint)

    def fallback():
        return _inspect_uploaded_image(image_b64, filename, category_hint)

    return _run_step("wonder", live, fallback)


# --------------------------------------------------------------------------- #
# Step 3: Muse Image
# --------------------------------------------------------------------------- #
def _extract_image_b64(data: dict) -> str:
    items = data.get("data") or []
    if items and items[0].get("b64_json"):
        return items[0]["b64_json"]
    if items and items[0].get("url"):
        img = requests.get(items[0]["url"], timeout=15)
        img.raise_for_status()
        return base64.b64encode(img.content).decode()
    raise ValueError("no image in response")


def synthesize_studio_with_muse_image(image_b64: str, product_title: str, sam_result: dict = None):
    def live():
        payload = {
            "model": MODELS["image"],
            "prompt": f"Clean commercial showcase photography of {product_title}, balanced studio lighting.",
            "init_image": image_b64,
            "strength": 0.35,
        }
        # Optional: pass the SAM mask along if the API returned one (verify field name in docs).
        if isinstance(sam_result, dict) and sam_result.get("mask"):
            payload["mask"] = sam_result["mask"]
        out = _extract_image_b64(_post("/images/generations", payload, 25))
        return {"enhanced_image_b64": out, "mime": _detect_mime(out)}

    return _run_step("image", live, lambda: _local_studio_enhance(image_b64))


# --------------------------------------------------------------------------- #
# Step 4: Muse Spark
# --------------------------------------------------------------------------- #
AD_KEYS = ("ad_copy_en", "ad_copy_rw", "ad_copy_fr")


def generate_ads_with_muse_spark(catalog: dict, location_name: str = "Kigali"):
    title = catalog.get("title", "Featured Item")
    price = catalog.get("estimated_price_rwf", "10,000")
    cat = catalog.get("category", "Local Service")

    def live():
        raw = _chat_json(
            MODELS["spark"],
            [
                {"role": "system", "content": (
                    "You write short WhatsApp promotions for Rwandan micro-merchants. Return JSON "
                    "with keys 'ad_copy_en', 'ad_copy_rw' (natural Kinyarwanda), 'ad_copy_fr'. "
                    "Each is 1-2 friendly sentences with the price in RWF and a call to message "
                    "on WhatsApp.")},
                {"role": "user", "content": f"{title} ({cat}), {price} RWF, located at {location_name}."},
            ],
            20,
        )
        out = {k: str(raw.get(k, "")).strip() for k in AD_KEYS}
        if not all(out.values()):
            raise ValueError("model reply missing one of the three languages")
        return out

    def fallback():
        return {
            "ad_copy_en": f"✨ {title} ({cat}) available in {location_name} for {price} RWF! "
                          "Message us on WhatsApp to book or order directly.",
            "ad_copy_rw": f"✨ {title} ({cat}) iboneka i {location_name} ku giciro cya {price} RWF! "
                          "Twandikire kuri WhatsApp utange komande cyangwa ufate gahunda.",
            "ad_copy_fr": f"✨ {title} ({cat}) disponible à {location_name} pour {price} RWF ! "
                          "Contactez-nous sur WhatsApp pour commander ou réserver.",
        }

    return _run_step("spark", live, fallback)
