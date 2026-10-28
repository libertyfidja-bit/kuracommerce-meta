import json
import requests

SERVER_URL = "http://127.0.0.1:5000"

def run_tests():
    print("--- 1. Testing Health Endpoint ---")
    res = requests.get(f"{SERVER_URL}/health")
    print("Status:", res.status_code)
    print("Response:", res.json())
    assert res.status_code == 200, "Health check failed!"

    # Ask the user to input their own WhatsApp number in the terminal
    user_number = input("\nEnter your WhatsApp phone number (e.g., +2507...): ").strip()
    while not user_number:
        user_number = input("Phone number cannot be empty! Please enter your WhatsApp number: ").strip()

    # 1x1 transparent sample pixel as base64
    dummy_pixel_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="

    print(f"\n--- 2. Testing /api/process-product for {user_number} ---")
    payload = {
        "whatsapp_number": user_number,
        "image_base64": dummy_pixel_b64
    }
    res = requests.post(f"{SERVER_URL}/api/process-product", json=payload)
    print("Status:", res.status_code)
    assert res.status_code == 200, "Process product endpoint failed!"

    print(f"\n--- 3. Testing /api/whatsapp-webhook for {user_number} ---")
    wa_payload = {
        "from": user_number,
        "image_base64": dummy_pixel_b64
    }
    wa_res = requests.post(f"{SERVER_URL}/api/whatsapp-webhook", json=wa_payload)
    print("WhatsApp Webhook Status:", wa_res.status_code)
    print("\nGenerated WhatsApp Message:")
    print(wa_res.json().get("whatsapp_formatted_message"))
    assert wa_res.status_code == 200, "WhatsApp webhook failed!"

    print("\nAll API tests completed successfully!")

if __name__ == "__main__":
    run_tests()