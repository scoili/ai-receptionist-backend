# agent_logic.py

import random
from memory import get_session

FILLERS = [
    "Hmm", "Alright", "Okay", "Let me see", "Just a moment", "Right"
]

def humanize(text):
    if random.random() < 0.4:
        return f"{random.choice(FILLERS)}… {text}"
    return text

def handle_message(message, session_id):
    session = get_session(session_id)
    msg = message.lower()

    # --------- INTENT DETECTION ----------
    if session["intent"] is None:
        if "appointment" in msg or "book" in msg:
            session["intent"] = "booking"
            return {"reply": humanize("Sure, I can help with that. What service are you looking for?")}
        else:
            return {"reply": humanize("Could you please tell me what you're calling about today?")}

    # --------- SERVICE ----------
    if session["service"] is None:
        session["service"] = message
        return {"reply": humanize("Got it. What date would you prefer?")}

    # --------- DATE ----------
    if session["date"] is None:
        session["date"] = message
        return {"reply": humanize("Thanks. May I have your name, please?")}

    # --------- NAME ----------
    if session["name"] is None:
        session["name"] = message
        return {
            "reply": humanize(
                f"Alright {session['name']}, just to confirm — you'd like to book {session['service']} on {session['date']}, correct?"
            ),
            "memory": session
        }

    # --------- CONFIRM ----------
    if "yes" in msg or "correct" in msg:
        return {
            "reply": humanize(
                "Perfect. I've booked that for you. You’ll receive a confirmation shortly. Anything else I can help with?"
            ),
            "memory": session
        }

    if "no" in msg:
        session["service"] = None
        session["date"] = None
        session["name"] = None
        return {"reply": humanize("No problem. Let’s start again. What service do you need?")}

    # --------- FALLBACK ----------
    return {"reply": humanize("Sorry, could you repeat that for me?")}
