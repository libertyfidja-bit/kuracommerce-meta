import hashlib
import logging
import os
import re
import secrets
import time
from concurrent.futures import ThreadPoolExecutor
from functools import wraps

from dotenv import load_dotenv

load_dotenv()  # must run before meta_client reads META_API_KEY

from flask import Flask, jsonify, render_template, request  # noqa: E402
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer  # noqa: E402

import meta_client as meta  # noqa: E402
import storage  # noqa: E402

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("kuracommerce")

app = Flask(__name__, template_folder="templates")
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # reject uploads over 8 MB

# --- Admin auth (server-side) ------------------------------------------------
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
if not ADMIN_PASSWORD:
    ADMIN_PASSWORD = secrets.token_urlsafe(8)
    log.warning("ADMIN_PASSWORD is not set. Temporary admin password for this run: %s", ADMIN_PASSWORD)
SECRET_KEY = os.getenv("SECRET_KEY") or hashlib.sha256(f"kura:{ADMIN_PASSWORD}".encode()).hexdigest()
_signer = URLSafeTimedSerializer(SECRET_KEY, salt="kuracommerce-admin")
TOKEN_MAX_AGE = 8 * 3600

storage.init_db()

DEFAULT_LOCATION = ("Kimironko Market, Kigali", -1.9487, 30.1262)
PHONE_RE = re.compile(r"^\+?\d{9,15}$")

# Reference points so the map is not empty. Clearly labelled as samples in the UI,
# with no phone numbers so nobody real is contacted.
SAMPLE_PLACES = [
    {"name": "Sample: Nyamirambo barber shop", "category": "Barber & Grooming Salon",
     "area": "Nyamirambo", "lat": -1.9782, "lng": 30.0447, "price": "5,000 RWF"},
    {"name": "Sample: Kimironko market stall", "category": "Local Market & Fresh Produce",
     "area": "Kimironko Market", "lat": -1.9487, "lng": 30.1262, "price": "3,500 RWF"},
    {"name": "Sample: Remera barber shop", "category": "Barber & Grooming Salon",
     "area": "Remera Gisimenti", "lat": -1.9592, "lng": 30.1095, "price": "6,000 RWF"},
    {"name": "Sample: Downtown kitenge tailor", "category": "Artisan Craft & Retail",
     "area": "Downtown Kigali", "lat": -1.9441, "lng": 30.0619, "price": "15,000 RWF"},
    {"name": "Sample: Nyabugogo market stall", "category": "Local Market & Fresh Produce",
     "area": "Nyabugogo", "lat": -1.9395, "lng": 30.0445, "price": "2,500 RWF"},
]


def require_admin(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        token = header[7:] if header.startswith("Bearer ") else ""
        try:
            _signer.loads(token, max_age=TOKEN_MAX_AGE)
        except (BadSignature, SignatureExpired):
            return jsonify({"error": "Admin login required."}), 401
        return fn(*args, **kwargs)
    return wrapper


def clean_phone(raw: str) -> str:
    return re.sub(r"[\s\-()]", "", raw or "")


def clean_coord(value, default, low, high):
    try:
        v = float(value)
        return v if low <= v <= high else default
    except (TypeError, ValueError):
        return default


# --- Pipeline ----------------------------------------------------------------
def run_pipeline(image_b64, filename, category, location_name, stock_qty):
    """SAM + Muse Wonder run in parallel; then Muse Image + Muse Spark run in parallel."""
    with ThreadPoolExecutor(max_workers=2) as pool:
        sam_f = pool.submit(meta.segment_product_with_sam, image_b64)
        wonder_f = pool.submit(meta.analyze_product_with_muse_wonder, image_b64, filename, category)
        (sam, sam_m), (catalog, wonder_m) = sam_f.result(), wonder_f.result()

        image_f = pool.submit(meta.synthesize_studio_with_muse_image, image_b64, catalog["title"], sam)
        spark_f = pool.submit(meta.generate_ads_with_muse_spark, catalog, location_name)
        (studio, image_m), (campaign, spark_m) = image_f.result(), spark_f.result()

    steps = [sam_m, wonder_m, image_m, spark_m]
    low_stock = stock_qty <= 2
    warning = f"\n\n⚠️ *Low Stock Alert:* Only {stock_qty} unit(s) left!" if low_stock else ""
    message = (
        f"✅ *KuraCommerce Listing Ready*\n\n"
        f"📦 *Item:* {catalog['title']}\n"
        f"📂 *Category:* {catalog['category']}\n"
        f"📍 *Location:* {location_name}\n"
        f"💰 *Price:* {catalog['estimated_price_rwf']} RWF\n"
        f"📊 *Stock:* {stock_qty} units{warning}\n\n"
        f"🇷🇼 *Kinyarwanda:*\n{campaign['ad_copy_rw']}\n\n"
        f"🇬🇧 *English:*\n{campaign['ad_copy_en']}\n\n"
        f"🇫🇷 *Français:*\n{campaign['ad_copy_fr']}"
    )
    return {
        "catalog": catalog,
        "campaign": campaign,
        "segmentation": sam,
        "studio_image": {"b64": studio["enhanced_image_b64"], "mime": studio.get("mime", "image/jpeg")},
        "pipeline": steps,
        "all_models_live": all(not s["fallback"] for s in steps),
        "low_stock": low_stock,
        "whatsapp_formatted_message": message,
    }


def store_result(phone, result, stock_qty, location_name, lat, lng):
    # Never store the image bytes, only text and telemetry.
    payload = {k: v for k, v in result.items() if k != "studio_image"}
    c = result["catalog"]
    return storage.save_listing(phone, c["title"], c["category"], c["estimated_price_rwf"],
                                stock_qty, location_name, lat, lng, payload)


# --- Routes ------------------------------------------------------------------
@app.get("/")
def index():
    return render_template("index.html")


@app.get("/health")
def health():
    return jsonify({"project": "KuraCommerce Hub", "status": "online"}), 200


@app.get("/api/status")
def status():
    """Lets anyone (judges included) see whether the real Meta models are wired up."""
    return jsonify({
        "meta_api_configured": meta.api_configured(),
        "meta_api_base": meta.current_base(),
        "provider": meta.PROVIDER_LABEL,
        "models": meta.MODELS,
        "live_steps": sorted(meta.LIVE_STEPS),
        "note": "If meta_api_configured is false, every step runs a local fallback.",
    })


@app.post("/api/process-product")
def process_product():
    data = request.get_json(silent=True) or {}
    image_b64 = (data.get("image_base64") or "").strip()
    phone = clean_phone(data.get("whatsapp_number"))
    if not PHONE_RE.match(phone):
        return jsonify({"error": "Enter a valid WhatsApp number, for example +250788000000."}), 400
    if not image_b64:
        return jsonify({"error": "Add a product photo first."}), 400
    try:
        stock_qty = max(0, min(int(data.get("stock_quantity", 5)), 10000))
    except (TypeError, ValueError):
        return jsonify({"error": "Stock quantity must be a whole number."}), 400

    location_name = (data.get("location_name") or DEFAULT_LOCATION[0]).strip()[:120]
    lat = clean_coord(data.get("lat"), DEFAULT_LOCATION[1], -90, 90)
    lng = clean_coord(data.get("lng"), DEFAULT_LOCATION[2], -180, 180)

    result = run_pipeline(image_b64, (data.get("filename") or "").strip()[:120],
                          (data.get("service_category") or "Product / Craft").strip()[:80],
                          location_name, stock_qty)
    listing_id = store_result(phone, result, stock_qty, location_name, lat, lng)
    return jsonify({"success": True, "listing_id": listing_id, "merchant_whatsapp": phone,
                    "location_name": location_name, "lat": lat, "lng": lng,
                    "stock_quantity": stock_qty, **result}), 200


@app.get("/api/listings")
def public_listings():
    items = [{**p, "phone": "", "sample": True} for p in SAMPLE_PLACES]
    for row in storage.list_listings(limit=200):
        items.append({"name": row["title"], "category": row["category"], "area": row["location_name"],
                      "lat": row["lat"], "lng": row["lng"], "price": f"{row['price']} RWF",
                      "phone": row["phone"], "stock": row["stock"], "sample": False})
    return jsonify(items)


# --- Admin -------------------------------------------------------------------
@app.post("/api/admin/login")
def admin_login():
    data = request.get_json(silent=True) or {}
    supplied = str(data.get("password", ""))
    if not secrets.compare_digest(supplied.encode(), ADMIN_PASSWORD.encode()):
        time.sleep(0.5)  # slow down guessing
        return jsonify({"error": "Incorrect password."}), 401
    return jsonify({"token": _signer.dumps({"role": "admin"}), "expires_in": TOKEN_MAX_AGE})


@app.post("/api/admin/model-endpoint")
def set_model_endpoint():
    """Point the app at a self-hosted model server (for example a Kaggle tunnel URL).

    Body: {"password": "...", "base_url": "https://xxx.trycloudflare.com/v1", "api_key": "..."}
    Held in memory only: it resets when the app restarts, so re-run it after a redeploy.
    """
    data = request.get_json(silent=True) or {}
    if not secrets.compare_digest(str(data.get("password", "")).encode(), ADMIN_PASSWORD.encode()):
        time.sleep(0.5)
        return jsonify({"error": "Incorrect password."}), 401
    base = str(data.get("base_url", "")).strip()
    if not re.match(r"^https://[\w.\-]+(:\d+)?(/[\w.\-/]*)?$", base):
        return jsonify({"error": "base_url must be an https URL, for example https://abc.trycloudflare.com/v1"}), 400
    meta.set_endpoint(base, data.get("api_key"))
    log.info("Model endpoint updated to %s", meta.current_base())
    return jsonify({"ok": True, "meta_api_base": meta.current_base()})


@app.get("/api/admin/listings")
@require_admin
def admin_listings():
    return jsonify(storage.list_listings(limit=200, with_payload=True))


# --- WhatsApp (simulator) ----------------------------------------------------
@app.get("/api/whatsapp-webhook")
def whatsapp_verify():
    """Verification handshake used by the WhatsApp Cloud API when you register a webhook."""
    token = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
    if token and request.args.get("hub.mode") == "subscribe" \
            and request.args.get("hub.verify_token") == token:
        return request.args.get("hub.challenge", ""), 200
    return "Forbidden", 403


@app.post("/api/whatsapp-webhook")
def whatsapp_receive():
    """Simulator: accepts {from, image_base64} and returns the message that WOULD be sent.

    It does not call the WhatsApp Cloud API: no media download, no outgoing message.
    """
    data = request.get_json(silent=True) or {}
    phone = clean_phone(data.get("from"))
    image_b64 = (data.get("image_base64") or "").strip()
    if not PHONE_RE.match(phone) or not image_b64:
        return jsonify({"error": "Provide 'from' (phone number) and 'image_base64'."}), 400
    result = run_pipeline(image_b64, "", "Product / Craft", DEFAULT_LOCATION[0], 5)
    store_result(phone, result, 5, DEFAULT_LOCATION[0], DEFAULT_LOCATION[1], DEFAULT_LOCATION[2])
    return jsonify({"simulated": True, "whatsapp_formatted_message": result["whatsapp_formatted_message"],
                    "pipeline": result["pipeline"]})


# --- USSD (simulator) --------------------------------------------------------
@app.post("/api/ussd-fallback")
def ussd_fallback():
    """Simulated *250# menu. Not connected to MTN/Airtel or any telecom gateway."""
    data = request.get_json(silent=True) or {}
    if (data.get("ussd_code") or "").strip() != "*250#":
        return jsonify({"error": "Invalid code. Dial *250# for the merchant menu."}), 400
    choice = (data.get("input") or "").strip()
    phone = clean_phone(data.get("phone"))

    if choice == "":
        text = ("CON KuraCommerce (*250#)\n1. Reference prices (RWF)\n2. Add a listing\n"
                "3. Low stock alerts\n4. Request delivery rider")
    elif choice == "1":
        text = "END Reference prices, Kigali:\n- Kitenge shirt: 15,000 RWF\n- Tomatoes (kg): 3,500 RWF\n- Haircut: 5,000 RWF"
    elif choice == "2":
        text = "END To add a listing, send a photo of your item on WhatsApp or use the web studio."
    elif choice == "3":
        low = storage.low_stock_for(phone) if phone else []
        if not phone:
            text = "END Enter your WhatsApp number in the studio first, then dial again."
        elif low:
            text = "END Low stock:\n" + "\n".join(f"- {i['title']}: {i['stock']} left" for i in low)
        else:
            text = "END No items are low on stock."
    elif choice == "4":
        text = "END Demo only: rider requests are not connected to a delivery service yet."
    else:
        text = "END Invalid option. Dial *250# to restart."

    return jsonify({"simulated": True, "session_active": text.startswith("CON"), "response_text": text})


@app.errorhandler(413)
def too_large(_):
    return jsonify({"error": "Photo is too large. Maximum upload is 8 MB."}), 413


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5001)),
            debug=os.environ.get("FLASK_DEBUG") == "1")
