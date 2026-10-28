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
    data = request.get_json(silent=True)
    if not data or "image_base64" not in data:
        return jsonify({"error": "Missing 'image_base64' in JSON body"}), 400

    raw_image = data["image_base64"]

    # 1. SAM 3.1: Isolate foreground craft
    sam_result = segment_product_with_sam(raw_image)

    # 2. Muse Wonder: Visual reasoning & price appraisal
    wonder_metadata = analyze_product_with_muse_wonder(raw_image)

    # 3. Muse Image: Studio background synthesis
    product_title = wonder_metadata.get("title", "Artisan Product")
    image_synthesis = synthesize_studio_with_muse_image(raw_image, product_title)

    # 4. Muse Spark: Multilingual WhatsApp ad copy (EN, RW, FR)
    spark_campaign = generate_ads_with_muse_spark(wonder_metadata)

    return jsonify({
        "success": True,
        "models_executed": ["sam-3.1", "muse-wonder", "muse-image", "muse-spark"],
        "segmentation_status": "processed",
        "sam_3_1_output": sam_result,
        "muse_wonder_catalog": wonder_metadata,
        "muse_image_studio": image_synthesis,
        "muse_spark_campaign": spark_campaign
    }), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
