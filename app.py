from flask import Flask, request, jsonify
from flask_cors import CORS
from agent_logic import handle_message
import uuid

app = Flask(__name__)
CORS(app)

@app.route("/", methods=["GET"])
def home():
    return "AI Receptionist backend is running."

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    message = data.get("message", "")
    session_id = data.get("session_id", str(uuid.uuid4()))

    response = handle_message(message, session_id)
    response["session_id"] = session_id

    return jsonify(response)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
