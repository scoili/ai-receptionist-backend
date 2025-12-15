import os
from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)

# Load API key
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise RuntimeError("OPENAI_API_KEY not set")

client = OpenAI(api_key=api_key)

SYSTEM_PROMPT = (
    "You are Mia, a warm, friendly AI receptionist for small businesses. "
    "You help callers book appointments and answer basic questions. "
    "Keep replies short, natural, and polite."
)

@app.route("/", methods=["GET"])
def home():
    return "AI Receptionist backend is running."

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json(force=True)

        user_message = data.get("message")
        if not user_message:
            return jsonify({"error": "message is required"}), 400

        response = client.responses.create(
            model="gpt-4.1-mini",
            input=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ]
        )

        reply = response.output_text

        return jsonify({"reply": reply})

    except Exception as e:
        print("CHAT ERROR:", str(e))  # 👈 this shows real error in Render logs
        return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
