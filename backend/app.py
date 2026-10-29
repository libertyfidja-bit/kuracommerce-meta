import os
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from meta_client import (
    segment_product_with_sam,
    analyze_product_with_muse_wonder,
    synthesize_studio_with_muse_image,
    generate_ads_with_muse_spark
)

load_dotenv()

# 1. Initialize Flask app FIRST
app = Flask(__name__, template_folder="templates")

# In-memory stores
ADMIN_CREDENTIALS = {"password": "admin123"}
inventory_database = {}

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "project": "KuraCommerce Hub",
        "track": "Indie Developer",
        "theme": "Build for Your World",
        "status": "online"
    }), 200

@app.route("/api/admin/reset-password", methods=["POST"])
def reset_admin_password():
    data = request.get_json(silent=True) or {}
    old_pwd = data.get("old_password", "")
    new_pwd = data.get("new_password", "")

    if old_pwd != ADMIN_CREDENTIALS["password"]:
        return jsonify({"error": "Current password is incorrect."}), 400
    if not new_pwd or len(new_pwd) < 4:
        return jsonify({"error": "New password must be at least 4 characters long."}), 400

    ADMIN_CREDENTIALS["password"] = new_pwd
    return jsonify({"success": True, "message": "Admin password updated successfully."}), 200

@app.route("/api/process-product", methods=["POST"])
def process_product():
    data = request.get_json(silent=True) or {}
    raw_image = data.get("image_base64", "").strip()
    user_phone = data.get("whatsapp_number", "").strip()
    filename = data.get("filename", "").strip()
    category_hint = data.get("service_category", "Product / Craft").strip()
    location_name = data.get("location_name", "Kimironko Market, Kigali").strip()
    stock_qty = int(data.get("stock_quantity", 5))
    lat = data.get("lat", -1.9487)
    lng = data.get("lng", 30.1262)

    if not user_phone:
        return jsonify({"error": "Please enter your WhatsApp phone number."}), 400
    if not raw_image:
        return jsonify({"error": "Missing image."}), 400

    sam_result = segment_product_with_sam(raw_image)
    wonder_metadata = analyze_product_with_muse_wonder(raw_image, filename, category_hint)
    product_title = wonder_metadata.get("title", "Featured Item")
    image_synthesis = synthesize_studio_with_muse_image(raw_image, product_title)
    spark_campaign = generate_ads_with_muse_spark(wonder_metadata, location_name)

    whatsapp_reply = (
        f"✅ *KuraCommerce AI Listing Active!*\n\n"
        f"📦 *Item:* {product_title}\n"
        f"📂 *Category:* {wonder_metadata.get('category')}\n"
        f"📍 *Location:* {location_name}\n"
        f"💰 *Price:* {wonder_metadata.get('estimated_price_rwf')} RWF\n"
        f"📊 *Stock:* {stock_qty} units\n\n"
        f"🇷🇼 {spark_campaign.get('ad_copy_rw')}\n\n"
        f"🇬🇧 {spark_campaign.get('ad_copy_en')}"
    )

    return jsonify({
        "success": True,
        "merchant_whatsapp": user_phone,
        "location_name": location_name,
        "stock_quantity": stock_qty,
        "muse_wonder_catalog": wonder_metadata,
        "whatsapp_formatted_message": whatsapp_reply
    }), 200

@app.route("/api/ussd-fallback", methods=["POST"])
def ussd_fallback():
    data = request.get_json(silent=True) or {}
    ussd_code = data.get("ussd_code", "").strip()
    user_input = data.get("input", "").strip()

    if not ussd_code.startswith("*250#"):
        return jsonify({"error": "Invalid code. Dial *250# for Rwandan Merchant USSD Services."}), 400

    if user_input == "":
        response_text = (
            "CON KuraCommerce Hub (*250#)\n"
            "1. Check Market Prices (RWF)\n"
            "2. Register Quick WhatsApp Listing\n"
            "3. Low Stock & Reorder Alerts\n"
            "4. Request Moto Delivery Rider"
        )
    elif user_input == "1":
        response_text = (
            "END Live Market Prices (Kigali):\n"
            "- Kitenge Fashion: 15,000 RWF\n"
            "- Fresh Tomatoes: 3,500 RWF\n"
            "- Barber Cut: 5,000 RWF"
        )
    elif user_input == "2":
        response_text = "END Listing Registered on KuraCommerce Map & WhatsApp."
    elif user_input == "3":
        response_text = "END Low Stock Status: All items monitored successfully."
    elif user_input == "4":
        response_text = "END Delivery Rider requested from nearest Kigali cooperative."
    else:
        response_text = "END Invalid option. Dial *250# to restart."

    return jsonify({
        "ussd_gateway": "MTN/Airtel Rwanda (*250#)",
        "session_active": not response_text.startswith("END"),
        "response_text": response_text
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5001)), debug=True)