from flask import Flask, request, jsonify
import random
import re

app = Flask(__name__)

# =========================
# Conversation Memory (Demo)
# =========================
sessions = {}

# =========================
# Human Language Banks
# =========================
FILLERS = [
    "Hmm", "Okay", "Alright", "Let me think",
    "Just a moment", "Right", "So", "Uh"
]

ACKS = [
    "Got it", "Okay", "Alright", "Sure", "That helps"
]

CLARIFIERS = [
    "May I know which doctor you’re referring to?",
    "Could you tell me which date you had in mind?",
    "Can I just confirm a few details with you?",
    "Which day were you planning to visit?"
]

ESCALATIONS = [
    "I don’t want to give you the wrong information. I’ll have our team confirm this.",
    "That depends on availability, so it would be best if our staff confirms.",
    "I’ll note this down and have someone from the clinic get back to you."
]

def pick(arr):
    return random.choice(arr)

# =========================
# Intent Helpers
# =========================
def has_date(text):
    return bool(re.search(r"\b(\d{1,2})(st|nd|rd|th)?\b", text)) or \
           any(word in text for word in ["today", "tomorrow", "monday", "tuesday",
                                          "wednesday", "thursday", "friday",
                                          "saturday", "sunday", "december", "january"])

# =========================
# Routes
# =========================
@app.route("/", methods=["GET"])
def home():
    return "AI Receptionist backend is running."

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    message = data.get("message", "").lower()
    session_id = data.get("session_id", "default")

    if session_id not in sessions:
        sessions[session_id] = {
            "name": None,
            "date": None,
            "service": None,
            "doctor": None
        }

    state = sessions[session_id]

    filler = pick(FILLERS)
    ack = pick(ACKS)

    # =========================
    # HUMAN-LIKE LOGIC
    # =========================

    # Asking about doctor availability
    if "doctor" in message and ("available" in message or "availability" in message):
        if has_date(message):
            reply = (
                f"{filler}… so about that date — schedules can vary, especially around holidays. "
                f"I don’t want to give you the wrong information. "
                f"{pick(CLARIFIERS)}"
            )
        else:
            reply = (
                f"{filler}… the doctor usually sees patients between 10 AM and 6 PM. "
                f"{pick(CLARIFIERS)}"
            )

    # Date mentioned
    elif has_date(message):
        state["date"] = message
        reply = (
            f"{ack}. {filler}… before I proceed, may I have your full name please?"
        )

    # Name provided
    elif "my name is" in message or "this is" in message:
        name = message.replace("my name is", "").replace("this is", "").strip()
        state["name"] = name
        reply = (
            f"Thanks, {name}. {filler}… are you looking for a general consultation "
            f"or something specific?"
        )

    # Service mentioned
    elif any(word in message for word in ["consultation", "checkup", "treatment", "appointment"]):
        state["service"] = message
        reply = (
            f"{ack}. {filler}… I’ve noted this down. "
            f"Our team will call you shortly to confirm availability."
        )

    # Pricing questions
    elif "price" in message or "fees" in message or "cost" in message:
        reply = (
            f"{filler}… charges usually depend on the doctor and type of visit. "
            f"{pick(ESCALATIONS)}"
        )

    # Fallback (out-of-line questions)
    else:
        reply = (
            f"{ack}. {filler}… let me make a note of this, "
            f"and someone from our team will get back to you shortly."
        )

    return jsonify({
        "reply": reply,
        "memory": state
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
