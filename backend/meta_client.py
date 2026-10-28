import os
import requests

META_API_BASE = "https://api.dev.meta.ai/v1"
API_KEY = os.getenv("META_API_KEY", "")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def segment_product_with_sam(image_b64: str) -> dict:
    """1. SAM 3.1: Isolates foreground artisan product from cluttered background."""
    url = f"{META_API_BASE}/vision/segment"
    payload = {
        "model": "sam-3.1",
        "image": image_b64,
        "mode": "automatic"
    }
    try:
        response = requests.post(url, headers=HEADERS, json=payload, timeout=25)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {
            "model_used": "sam-3.1",
            "mask_isolated": True,
            "confidence": 0.98,
            "bounding_box": [45, 60, 480, 520],
            "status": f"Fallback active ({str(e)})"
        }

def analyze_product_with_muse_wonder(image_b64: str) -> dict:
    """2. Muse Wonder: Deep multimodal reasoning for product valuation and attribute extraction."""
    url = f"{META_API_BASE}/chat/completions"
    payload = {
        "model": "muse-wonder",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an expert product appraiser for Rwandan artisan goods. "
                    "Return strict JSON with keys: 'title', 'category', 'materials_detected', 'estimated_price_rwf'."
                )
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Inspect this segmented item and extract commercial catalog attributes."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
                ]
            }
        ],
        "response_format": {"type": "json_object"}
    }
    try:
        response = requests.post(url, headers=HEADERS, json=payload, timeout=25)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {
            "model_used": "muse-wonder",
            "title": "Handwoven Rwandan Agaseke Peace Basket",
            "category": "Home Decor & Artisan Crafts",
            "materials_detected": ["Natural Sisal Fiber", "Sweetgrass", "Organic Dye"],
            "estimated_price_rwf": "18,500",
            "status": f"Fallback active ({str(e)})"
        }

def synthesize_studio_with_muse_image(isolated_image_b64: str, product_title: str) -> dict:
    """3. Muse Image: Generates a clean commercial studio backdrop around the segmented item."""
    url = f"{META_API_BASE}/images/generations"
    payload = {
        "model": "muse-image",
        "prompt": (
            f"Professional commercial studio product photography of {product_title}, "
            "soft warm lighting, clean minimalist wooden surface, high resolution catalog style."
        ),
        "init_image": isolated_image_b64,
        "strength": 0.35
    }
    try:
        response = requests.post(url, headers=HEADERS, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {
            "model_used": "muse-image",
            "studio_enhancement": "applied",
            "lighting_preset": "warm_studio_softbox",
            "enhanced_image_b64": isolated_image_b64,
            "status": f"Fallback active ({str(e)})"
        }

def generate_ads_with_muse_spark(product_metadata: dict) -> dict:
    """4. Muse Spark: Fast multilingual copy generation for WhatsApp & social commerce."""
    url = f"{META_API_BASE}/chat/completions"
    payload = {
        "model": "muse-spark",
        "messages": [
            {
                "role": "system",
                "content": (
                    "Generate high-converting WhatsApp marketing copy in JSON with keys: "
                    "'ad_copy_en' (English), 'ad_copy_rw' (Kinyarwanda), 'ad_copy_fr' (French), and 'whatsapp_hashtags'."
                )
            },
            {
                "role": "user",
                "content": f"Create localized ad copy for this product: {product_metadata}"
            }
        ],
        "response_format": {"type": "json_object"}
    }
    try:
        response = requests.post(url, headers=HEADERS, json=payload, timeout=20)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {
            "model_used": "muse-spark",
            "ad_copy_en": "Authentic handwoven Rwandan Agaseke basket crafted from natural sisal. Order directly via WhatsApp!",
            "ad_copy_rw": "Agaseke k'umwimerere gakozwe mu mugwegwe n'abanyabukorikori b'Abanyarwanda. Tanga komande kuri WhatsApp!",
            "ad_copy_fr": "Panier Agaseke rwandais authentique tissé à la main en sisal naturel. Commandez sur WhatsApp !",
            "whatsapp_hashtags": ["#MadeInRwanda", "#Agaseke", "#KigaliCrafts", "#KuraCommerce"],
            "status": f"Fallback active ({str(e)})"
        }
