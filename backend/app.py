@app.route("/api/ussd-fallback", methods=["POST"])
def ussd_fallback():
    data = request.get_json(silent=True) or {}
    ussd_code = data.get("ussd_code", "").strip()
    user_input = data.get("input", "").strip()

    if not ussd_code.startswith("*250#"):
        return jsonify({"error": "Invalid code. Please dial *250# for Rwandan Merchant USSD Services."}), 400

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
            "- Barber Cut / Grooming: 5,000 RWF\n"
            "Data sent via SMS/USSD gateway."
        )
    elif user_input == "2":
        response_text = (
            "END Listing Registered!\n"
            "Your product/service is now active on KuraCommerce Map & WhatsApp."
        )
    elif user_input == "3":
        response_text = (
            "END Low Stock Status:\n"
            "⚠️ 1 item is low in stock. WhatsApp alert dispatched to merchant."
        )
    elif user_input == "4":
        response_text = (
            "END Delivery Rider Requested:\n"
            "Nearest Boda Boda cooperative in Kigali notified for pickup."
        )
    else:
        response_text = "END Invalid option selected. Dial *250# to restart."

    return jsonify({
        "ussd_gateway": "MTN/Airtel Rwanda Emulation (*250#)",
        "session_active": not response_text.startswith("END"),
        "response_text": response_text
    }), 200