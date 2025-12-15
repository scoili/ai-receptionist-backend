import os
from flask import Flask, request, jsonify
from openai import OpenAI

# Initialize app
app = Flask(__name__)

# OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """
You are a warm, friendly, professional AI receptionist named "Mia".

Your job:
- Greet callers politely
- Understand what service they want
- Help book appointments or collect details
- Keep responses short, natural, and human-like
"""

# Home route
@app.route("/", methods=["GET"])
def home():
    return "AI Receptionist backend is running."

# Health check
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

# Chat endpoint
@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()

        if not data or "message" not in data:
            return jsonify({"error": "Message is required"}), 400

        user_message = data["message"]

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            temperature=0.4
        )

        reply = response.choices[0].message.content

        return jsonify({"reply": reply})

    except Exception as e:
        # IMPORTANT: shows real error in Render logs
        print("ERROR:", str(e))
        return jsonify({"error": "Internal server error"}), 500


# Required for Render
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
