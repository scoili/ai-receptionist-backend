# memory.py

sessions = {}

def get_session(session_id):
    if session_id not in sessions:
        sessions[session_id] = {
            "intent": None,
            "service": None,
            "date": None,
            "name": None,
            "step": "start"
        }
    return sessions[session_id]

