import os
from flask import Flask, request, jsonify
from openai import OpenAI

# -------------------------
# App & Client Setup
# -------------------------

app = Flask(__name__)

# OpenAI client (API key is read from Render Environment Variables)
client = OpenAI()

# -------------------------
# System Prompt (Personality)
# -------------------------

SYSTEM_PROMPT = """
You are a warm, friendly, professional AI receptionist named Mia.

You answer calls for small businesses in the USA and Canada.

Guidelines:
- Speak in clear, natural American English
- Be polite, confident, and calm
- Keep replies short and human
- Avoid robotic language
- Use phrases like: "Sure", "Absolutely", "No problem", "Let me check"
- Your job is to understand what the caller needs and respond helpfully
"""

# -------------------------
# Health Check (IMPORTANT)
# -------------------------

@app.route("/health", methods=["GET"])
def health():
    return "OK", 200

# -------------------------
# Chat Endpoint (AI Brain)
# -------------------------

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json

    user_message = data.get("message", "")

    if not user_message:
        return jsonify({"error": "Message is required"}), 400

    try:
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
        return jsonify({"error": str(e)}), 500

# -------------------------
# Local Run (Not used by Render, but safe)
# -------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
