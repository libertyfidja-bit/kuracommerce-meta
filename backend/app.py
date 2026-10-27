import os
from flask import Flask, request, jsonify
from meta_client import segment_product_with_sam, generate_catalog_with_muse

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "project": "KuraCommerce",
        "track": "Indie Developer",
        "theme": "Build for Your World",
        "status": "online"
    }), 200

@app.route("/api/process-product", methods=["POST"])
def process_product():
    data = request.get_json(silent=True)
    if not data or "image_base64" not in data:
        return jsonify({"error": "Missing 'image_base64' in JSON body"}), 400

    raw_image = data["image_base64"]

    # Step 1: Run segmentation with SAM 3.1
    segmentation = segment_product_with_sam(raw_image)

    # Step 2: Extract attributes & generate multilingual copy with Muse Wonder
    catalog_info = generate_catalog_with_muse(raw_image)

    return jsonify({
        "success": True,
        "segmentation_status": "processed",
        "sam_output": segmentation,
        "catalog_metadata": catalog_info
    }), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
