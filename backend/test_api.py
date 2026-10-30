"""CLI tests. Usage:

    python test_api.py                                   # local server on :5001
    SERVER_URL=https://your-app.onrender.com python test_api.py
    ADMIN_PASSWORD=... python test_api.py                # also tests admin routes
"""
import base64
import io
import os

import requests

SERVER_URL = os.getenv("SERVER_URL", "http://127.0.0.1:5001").rstrip("/")
PHONE = os.getenv("TEST_PHONE", "+250788000000")


def test_image_b64():
    from PIL import Image
    img = Image.new("RGB", (256, 256), (200, 90, 40))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return base64.b64encode(buf.getvalue()).decode()


def run_tests():
    print("1. health and status")
    assert requests.get(f"{SERVER_URL}/health", timeout=60).status_code == 200  # long timeout: cold starts
    status = requests.get(f"{SERVER_URL}/api/status", timeout=30).json()
    print("   API configured:", status["meta_api_configured"], "| provider:", status.get("provider"), "| live steps:", status.get("live_steps"), "| models:", status["models"])

    print("2. process-product")
    img = test_image_b64()
    r = requests.post(f"{SERVER_URL}/api/process-product", timeout=120, json={
        "whatsapp_number": PHONE, "image_base64": img, "filename": "kitenge_shirt.jpg",
        "service_category": "Fashion & Custom Tailoring", "stock_quantity": 2})
    assert r.status_code == 200, r.text[:300]
    d = r.json()
    for key in ("title", "category", "estimated_price_rwf", "description"):
        assert d["catalog"].get(key), f"catalog missing {key}"
    for key in ("ad_copy_en", "ad_copy_rw", "ad_copy_fr"):
        assert d["campaign"].get(key), f"campaign missing {key}"
    assert d["low_stock"] and "Low Stock Alert" in d["whatsapp_formatted_message"]
    assert d["studio_image"]["b64"], "no studio image returned"
    for s in d["pipeline"]:
        print(f"   {s['step']:<7} {s['model']:<12} {s['source']:<9} {s['ms']} ms  {s['error'] or ''}")
    print("   RESULT:", "every step answered by a live model" if d["all_models_live"] else "local fallback used for at least one step (see list above)")

    print("3. validation")
    assert requests.post(f"{SERVER_URL}/api/process-product", json={"image_base64": img}, timeout=30).status_code == 400
    assert requests.post(f"{SERVER_URL}/api/process-product", json={"whatsapp_number": PHONE}, timeout=30).status_code == 400
    assert requests.post(f"{SERVER_URL}/api/process-product", json={"whatsapp_number": "abc", "image_base64": img}, timeout=30).status_code == 400
    assert requests.post(f"{SERVER_URL}/api/process-product", json={"whatsapp_number": PHONE, "image_base64": img, "stock_quantity": "x"}, timeout=30).status_code == 400

    print("4. public listings include the new listing")
    items = requests.get(f"{SERVER_URL}/api/listings", timeout=30).json()
    assert any(not i["sample"] for i in items), "saved listing missing"

    print("5. USSD simulator")
    u = lambda **kw: requests.post(f"{SERVER_URL}/api/ussd-fallback", json={"ussd_code": "*250#", **kw}, timeout=30)
    assert u(input="").json()["session_active"] is True
    assert u(input="1").json()["response_text"].startswith("END")
    assert "left" in u(input="3", phone=PHONE).json()["response_text"]
    assert requests.post(f"{SERVER_URL}/api/ussd-fallback", json={"ussd_code": "*999#"}, timeout=30).status_code == 400

    print("6. WhatsApp webhook simulator")
    w = requests.post(f"{SERVER_URL}/api/whatsapp-webhook", json={"from": PHONE, "image_base64": img}, timeout=120)
    assert w.status_code == 200 and w.json()["simulated"] is True

    print("7. admin auth")
    assert requests.get(f"{SERVER_URL}/api/admin/listings", timeout=30).status_code == 401
    assert requests.post(f"{SERVER_URL}/api/admin/login", json={"password": "wrong"}, timeout=30).status_code == 401
    pwd = os.getenv("ADMIN_PASSWORD")
    if pwd:
        tok = requests.post(f"{SERVER_URL}/api/admin/login", json={"password": pwd}, timeout=30).json()["token"]
        rows = requests.get(f"{SERVER_URL}/api/admin/listings", headers={"Authorization": f"Bearer {tok}"}, timeout=30)
        assert rows.status_code == 200 and rows.json()
    else:
        print("   (set ADMIN_PASSWORD to test the signed-in path)")

    print("\nAll tests passed.")


if __name__ == "__main__":
    run_tests()
