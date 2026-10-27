import os
import requests

META_API_BASE = "https://api.dev.meta.ai/v1"
API_KEY = os.getenv("META_API_KEY", "")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def segment_product_with_sam(image_b64: str) -> dict:
    """Uses SAM 3.1 via Meta Model API to isolate the product from cluttered backgrounds."""
    url = f"{META_API_BASE}/vision/segment"
    payload = {
        "model": "sam-3.1",
        "image": image_b64,
        "mode": "automatic"
    }
    try:
        response = requests.post(url, headers=HEADERS, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e), "mock_fallback": True, "mask_detected": True}

def generate_catalog_with_muse(image_b64: str) -> dict:
    """Uses Muse Wonder to analyze visual traits and produce pricing, tags, and multilingual ad copy."""
    url = f"{META_API_BASE}/chat/completions"
    payload = {
        "model": "muse-wonder",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are KuraCommerce Studio. Given an isolated product image from an artisan in Rwanda, "
                    "output strict JSON containing: 'title', 'category', 'estimated_price_rwf', "
                    "'ad_copy_en', 'ad_copy_rw' (Kinyarwanda)."
                )
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Analyze this handcrafted product and generate marketing metadata."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
                ]
            }
        ],
        "response_format": {"type": "json_object"}
    }
    try:
        response = requests.post(url, headers=HEADERS, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {
            "title": "Handcrafted Rwandan Agaseke Basket",
            "category": "Home Decor & Crafts",
            "estimated_price_rwf": "15,000",
            "ad_copy_en": "Authentic handmade Agaseke basket woven with natural sisal fibers.",
            "ad_copy_rw": "Agaseke keza gakozwe mu mugwegwe gakozwe n'abanyabukorikori bo mu Rwanda.",
            "note": f"Mock response (Error: {str(e)})"
        }
