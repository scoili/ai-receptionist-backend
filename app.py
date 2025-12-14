import os
from flask import Flask, request, jsonify
from openai import OpenAI

# Initialize Flask
app = Flask(__name__)

# Initialize OpenAI client (API key comes from Render ENV variable)
client = OpenAI()

# -----------------------
# BASIC ROUTES
# -----------------------

@app.route("/", methods=["GET"])
def home():
    return "AI Receptionist backend is running.", 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


# -----------------------
# AI CHAT ENDPOINT
# -----------------------

SYSTEM_PROMPT = """
You are a warm, friendly, professional AI receptionist named Mia.
You answer calls for small businesses in the USA and Canada.
Speak clearly, politely, and confidently.
Keep replies short, natural, and human.
"""

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message", "")

    if not user_message:
        return jsonify({"error": "Message is required"}), 400

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]
    )

    reply = response.choices[0].message.content
    return jsonify({"reply": reply})


# -----------------------
# START SERVER (LOCAL ONLY)
# -----------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
