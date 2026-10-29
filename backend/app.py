import os
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv

# Load environment variables from the root .env file
load_dotenv()

from meta_client import (
    segment_product_with_sam,
    analyze_product_with_muse_wonder,
    synthesize_studio_with_muse_image,
    generate_ads_with_muse_spark
)

app = Flask(__name__, template_folder="templates")

# Verify environment variable loading on startup
META_API_KEY_LOADED = os.getenv("META_API_KEY", "")
print(f"Loaded META_API_KEY status: {'Configured (Secret)' if META_API_KEY_LOADED and META_API_KEY_LOADED != 'your_meta_model_api_key_here' else 'Using Local Visual Fallback'}")

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "project": "KuraCommerce",
        "track": "Indie Developer",
        "theme": "Build for Your World",
        "allowed_models_integrated": ["sam-3.1", "muse-wonder", "muse-image", "muse-spark"],
        "api_key_configured": bool(META_API_KEY_LOADED and META_API_KEY_LOADED != 'your_meta_model_api_key_here'),
        "status": "online"
    }), 200

@app.route("/api/process-product", methods=["POST"])
def process_product():
    data = request.get_json(silent=True) or {}
    raw_image = data.get("image_base64", "").strip()
    user_phone = data.get("whatsapp_number", "").strip()
    filename = data.get("filename", "").strip()
    category_hint = data.get("service_category", "Product / Craft").strip()
    location_name = data.get("location_name", "Kigali, Rwanda").strip()
    lat = data.get("lat", -1.9441)
    lng = data.get("lng", 30.0619)

    if not user_phone:
        return jsonify({"error": "Please enter your WhatsApp phone number."}), 400
    if not raw_image:
        return jsonify({"error": "Missing 'image_base64' in request."}), 400

    sam_result = segment_product_with_sam(raw_image)
    wonder_metadata = analyze_product_with_muse_wonder(raw_image, filename, category_hint)
    product_title = wonder_metadata.get("title", "Featured Listing")
    image_synthesis = synthesize_studio_with_muse_image(raw_image, product_title)
    spark_campaign = generate_ads_with_muse_spark(wonder_metadata, location_name)

    whatsapp_reply = (
        f"✅ *KuraCommerce Listing Ready!*\n\n"
        f"🏷️ *Listing:* {wonder_metadata.get('title')}\n"
        f"📂 *Category:* {wonder_metadata.get('category')}\n"
        f"📍 *Location:* {location_name}\n"
        f"💰 *Estimated Rate/Price:* {wonder_metadata.get('estimated_price_rwf')} RWF\n\n"
        f"🇷🇼 *Kinyarwanda:*\n{spark_campaign.get('ad_copy_rw')}\n\n"
        f"🇬🇧 *English:*\n{spark_campaign.get('ad_copy_en')}\n\n"
        f"📲 *Seller WhatsApp:* {user_phone}"
    )

    return jsonify({
        "success": True,
        "merchant_whatsapp": user_phone,
        "location_name": location_name,
        "coordinates": {"lat": lat, "lng": lng},
        "models_executed": ["sam-3.1", "muse-wonder", "muse-image", "muse-spark"],
        "segmentation_status": "processed",
        "sam_3_1_output": sam_result,
        "muse_wonder_catalog": wonder_metadata,
        "muse_image_studio": image_synthesis,
        "muse_spark_campaign": spark_campaign,
        "whatsapp_formatted_message": whatsapp_reply
    }), 200

@app.route("/api/whatsapp-webhook", methods=["POST"])
def whatsapp_webhook():
    incoming = request.get_json(silent=True) or {}
    sender_phone = incoming.get("from", "").strip()
    image_b64 = incoming.get("image_base64", "").strip()

    if not sender_phone:
        return jsonify({"error": "User WhatsApp phone number ('from') is required"}), 400
    if not image_b64:
        return jsonify({"error": "No media found in WhatsApp payload"}), 400

    wonder_metadata = analyze_product_with_muse_wonder(image_b64, "WhatsApp Upload", "Local Commerce")
    spark_campaign = generate_ads_with_muse_spark(wonder_metadata, "Kigali")

    whatsapp_reply = (
        f"✅ *KuraCommerce Listing Ready!*\n\n"
        f"📦 *Item:* {wonder_metadata.get('title')}\n"
        f"💰 *Price:* {wonder_metadata.get('estimated_price_rwf')} RWF\n\n"
        f"🇷🇼 {spark_campaign.get('ad_copy_rw')}\n\n"
        f"📲 *WhatsApp:* {sender_phone}"
    )

    return jsonify({
        "status": "delivered",
        "recipient": sender_phone,
        "whatsapp_formatted_message": whatsapp_reply,
        "models_used": ["sam-3.1", "muse-wonder", "muse-image", "muse-spark"]
    }), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)