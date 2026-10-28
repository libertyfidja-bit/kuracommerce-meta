import os
from flask import Flask, request, jsonify, render_template
from meta_client import (
    segment_product_with_sam,
    analyze_product_with_muse_wonder,
    synthesize_studio_with_muse_image,
    generate_ads_with_muse_spark
)

app = Flask(__name__, template_folder="templates")

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "project": "KuraCommerce",
        "track": "Indie Developer",
        "theme": "Build for Your World",
        "allowed_models_integrated": [
            "sam-3.1",
            "muse-wonder",
            "muse-image",
            "muse-spark"
        ],
        "status": "online"
    }), 200

@app.route("/api/process-product", methods=["POST"])
def process_product():
    data = request.get_json(silent=True) or {}
    raw_image = data.get("image_base64", "").strip()
    user_phone = data.get("whatsapp_number", "").strip()

    if not user_phone:
        return jsonify({"error": "Please enter your WhatsApp phone number."}), 400
    if not raw_image:
        return jsonify({"error": "Missing 'image_base64' in request."}), 400

    # 1. SAM 3.1: Isolate foreground craft
    sam_result = segment_product_with_sam(raw_image)

    # 2. Muse Wonder: Visual reasoning & price appraisal
    wonder_metadata = analyze_product_with_muse_wonder(raw_image)

    # 3. Muse Image: Studio background synthesis
    product_title = wonder_metadata.get("title", "Artisan Product")
    image_synthesis = synthesize_studio_with_muse_image(raw_image, product_title)

    # 4. Muse Spark: Multilingual WhatsApp ad copy (EN, RW, FR)
    spark_campaign = generate_ads_with_muse_spark(wonder_metadata)

    whatsapp_reply = (
        f"✅ *KuraCommerce Studio Ready for {user_phone}!*\n\n"
        f"📦 *Product:* {wonder_metadata.get('title')}\n"
        f"💰 *Suggested Price:* {wonder_metadata.get('estimated_price_rwf')} RWF\n\n"
        f"🇷🇼 *Kinyarwanda Ad:*\n{spark_campaign.get('ad_copy_rw')}\n\n"
        f"🇬🇧 *English Ad:*\n{spark_campaign.get('ad_copy_en')}\n\n"
        f"📲 *Order via WhatsApp:* {user_phone}"
    )

    return jsonify({
        "success": True,
        "merchant_whatsapp": user_phone,
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
    """Handles incoming WhatsApp payloads and requires a valid user phone number."""
    incoming = request.get_json(silent=True) or {}
    sender_phone = incoming.get("from", "").strip()
    image_b64 = incoming.get("image_base64", "").strip()

    if not sender_phone:
        return jsonify({"error": "User WhatsApp phone number ('from') is required"}), 400
    if not image_b64:
        return jsonify({"error": "No media found in WhatsApp payload"}), 400

    sam_result = segment_product_with_sam(image_b64)
    wonder_metadata = analyze_product_with_muse_wonder(image_b64)
    product_title = wonder_metadata.get("title", "Artisan Product")
    image_synthesis = synthesize_studio_with_muse_image(image_b64, product_title)
    spark_campaign = generate_ads_with_muse_spark(wonder_metadata)

    whatsapp_reply = (
        f"✅ *KuraCommerce Studio Ready!*\n\n"
        f"📦 *Product:* {wonder_metadata.get('title')}\n"
        f"💰 *Suggested Price:* {wonder_metadata.get('estimated_price_rwf')} RWF\n\n"
        f"🇷🇼 *Kinyarwanda Ad:*\n{spark_campaign.get('ad_copy_rw')}\n\n"
        f"🇬🇧 *English Ad:*\n{spark_campaign.get('ad_copy_en')}\n\n"
        f"📲 *Contact Seller on WhatsApp:* {sender_phone}"
    )

    return jsonify({
        "status": "delivered",
        "recipient": sender_phone,
        "whatsapp_formatted_message": whatsapp_reply,
        "models_used": ["sam-3.1", "muse-wonder", "muse-image", "muse-spark"]
    }), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)