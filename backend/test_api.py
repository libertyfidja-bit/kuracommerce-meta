import base64
import requests

SERVER_URL = "http://127.0.0.1:5000"

def run_tests():
    print("--- 1. Testing Health Endpoint ---")
    res = requests.get(f"{SERVER_URL}/")
    print("Status:", res.status_code)
    print("Response:", res.json())
    assert res.status_code == 200, "Health check failed!"

    print("\n--- 2. Testing /api/process-product ---")
    # 1x1 transparent dummy pixel as base64
    dummy_pixel_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="

    payload = {
        "image_base64": dummy_pixel_b64
    }

    res = requests.post(f"{SERVER_URL}/api/process-product", json=payload)
    print("Status:", res.status_code)
    print("Response JSON:")
    import json
    print(json.dumps(res.json(), indent=2))
    assert res.status_code == 200, "Process product endpoint failed!"

    print("\nAll API tests completed successfully!")

if __name__ == "__main__":
    run_tests()
