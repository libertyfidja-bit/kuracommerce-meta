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

# ... (keep your existing /api/process-product and other routes below)