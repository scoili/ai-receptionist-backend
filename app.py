from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "AI Receptionist backend is running."

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        user_message = data.get("message", "").lower()

        # Demo AI logic (rule-based, realistic)
        if "book" in user_message or "appointment" in user_message:
            reply = "Sure! I can help you book an appointment. May I have your full name please?"
        elif "name" in user_message:
            reply = "Thank you. What service are you looking for today?"
        elif "hair" in user_message or "spa" in user_message or "consult" in user_message:
            reply = "Got it. What date and time would you prefer?"
        elif "today" in user_message or "tomorrow" in user_message:
            reply = "Perfect. I have noted your request. Our team will contact you shortly to confirm."
        elif "price" in user_message or "cost" in user_message:
            reply = "Prices vary based on service. May I know which service you are interested in?"
        else:
            reply = "Sure, I understand. Let me note this and have our team follow up with you."

        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
