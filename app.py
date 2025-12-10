import os
from flask import Flask, request, Response
from datetime import datetime
from openai import OpenAI

# OpenAI client
client = OpenAI()

app = Flask(__name__)

# In-memory store for calls. Later we can replace this with a database.
CALL_CONVERSATIONS = {}

SYSTEM_PROMPT = """
You are a warm, friendly, professional, and confident AI receptionist named “Mia.” 
Your job is to answer incoming calls for small service businesses in the USA and Canada. 

VOICE & PERSONALITY:
- Speak in clear, natural American English.
- Warm, welcoming, and polite at all times.
- Confident and helpful, like a trained office assistant.
- Keep responses short, human, and conversational.
- Avoid robotic or overly formal language.
- Use small natural phrases: “Absolutely,” “Sounds good,” “No problem,” “Let me check,” etc.

GOALS:
1. Greet the caller immediately and make them feel comfortable.
2. Understand what service they need.
3. Collect the caller’s:
   - Name
   - Phone number (if not provided)
   - Service request details
   - Address or city (if required)
   - Preferred time for service or appointment
4. If the caller has an emergency (plumbing burst, AC broken, roof leak, etc), respond urgently.
5. If the caller asks about pricing, give general guidance without quoting exact prices unless provided by the business.
6. After collecting details, tell the caller:
   “I’ve sent your details to the team. Someone will contact you shortly. Thank you for calling!”

BEHAVIOR RULES:
- Always sound calm and confident.
- Do NOT mention you are an AI.
- Do NOT transfer the call.
- If the caller is confused, repeat simply and clearly.
- If the caller asks who you are: 
  “I’m Mia, the virtual receptionist for the business. How can I help you today?”
- Never provide medical, legal, or financial advice.
- Redirect complicated questions: 
  “I’ll note that down for the team to assist you.”

CALL FLOW:
1. Greeting example:
   “Hi! Thanks for calling. This is Mia, how can I help you today?”

2. After they explain:
   - Show empathy if needed: “I’m sorry to hear that, let’s get that taken care of.”
   - Ask clarifying questions to fully understand the issue.

3. Lead capture questions:
   - “May I have your name?”
   - “What’s the best number to reach you at?”
   - “Could you tell me a bit more about the issue?”
   - “Where are you located?”
   - “When would be a good time for our technician/agent to reach you?”

4. Wrap-up:
   “Perfect, I’ve noted everything. Our team will contact you shortly to confirm the next steps. Thank you for calling!”

FAILSAFE RULES:
- If you don’t understand the caller, say:
  “I’m sorry, could you repeat that for me?”
- If the caller becomes angry, stay calm:
  “I understand, I’m here to help. Let’s sort this out together.”
- If the conversation goes off-topic:
  “I’ll make a note of that. For now, let me just gather the service details.”

Your mission is to sound HUMAN, trustworthy, and helpful at all times.
"""


def get_conversation(call_sid: str):
    """
    Get or create a conversation object for a specific call.
    """
    if call_sid not in CALL_CONVERSATIONS:
        CALL_CONVERSATIONS[call_sid] = {
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT}
            ]
        }
    return CALL_CONVERSATIONS[call_sid]


def call_openai(messages):
    """
    Ask OpenAI what the assistant should say next.
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.4,
    )
    return response.choices[0].message.content


@app.route("/", methods=["GET"])
def health():
    return "AI Receptionist backend is running."


@app.route("/voice", methods=["POST"])
def voice():
    """
    This is the webhook Twilio will call when someone dials the business number.
    It returns TwiML (XML) telling Twilio what to say and how to listen.
    """
    call_sid = request.values.get("CallSid", "")
    from_number = request.values.get("From", "")
    conv = get_conversation(call_sid)

    # First turn: greet and start conversation
    conv["messages"].append({
        "role": "user",
        "content": f"A new caller is on the line. Their phone number is {from_number}. Greet them and start the conversation."
    })

    ai_reply = call_openai(conv["messages"])
    conv["messages"].append({"role": "assistant", "content": ai_reply})

    # We build TwiML manually as a string.
    # We will use <Gather> with speech input so Twilio listens for caller speech.
    # For voice, we pick a natural American English voice (e.g., Polly.Joanna).
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Gather input="speech"
          action="/handle_input"
          method="POST"
          speechTimeout="auto">
    <Say voice="Polly.Joanna">{ai_reply}</Say>
  </Gather>
  <Say voice="Polly.Joanna">Sorry, I did not receive any input. Goodbye.</Say>
  <Hangup/>
</Response>
"""
    return Response(twiml, mimetype="text/xml")


@app.route("/handle_input", methods=["POST"])
def handle_input():
    """
    Handles each reply from the caller (their speech).
    Twilio sends us SpeechResult (the transcript).
    """
    call_sid = request.values.get("CallSid", "")
    speech_result = request.values.get("SpeechResult", "")
    from_number = request.values.get("From", "")

    conv = get_conversation(call_sid)

    if not speech_result:
        # If Twilio didn't understand anything, ask again
        twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Gather input="speech"
          action="/handle_input"
          method="POST"
          speechTimeout="auto">
    <Say voice="Polly.Joanna">I’m sorry, I didn’t catch that. Could you please repeat?</Say>
  </Gather>
  <Say voice="Polly.Joanna">Sorry, I still did not receive any input. Goodbye.</Say>
  <Hangup/>
</Response>
"""
        return Response(twiml, mimetype="text/xml")

    # Add caller's speech to conversation
    conv["messages"].append({"role": "user", "content": speech_result})

    # Ask OpenAI what to respond and whether to continue or end
    control_prompt = """
Given the conversation so far with the caller, decide whether you:
- should ask the caller another follow-up question to clarify or collect more info, OR
- have enough information and should politely end the call.

Reply in JSON with:
{
  "action": "continue" or "end",
  "assistant_reply": "what you will say to the caller next"
}
Keep the reply short, friendly, and conversational.
"""
    control_messages = conv["messages"] + [
        {"role": "user", "content": control_prompt}
    ]

    control_raw = call_openai(control_messages)

    # Defaults
    action = "continue"
    assistant_reply = control_raw

    # Try to parse JSON
    try:
        import json
        parsed = json.loads(control_raw)
        action = parsed.get("action", "continue")
        assistant_reply = parsed.get("assistant_reply", assistant_reply)
    except Exception:
        # If parsing fails, just use the raw text
        pass

    # Save assistant reply
    conv["messages"].append({"role": "assistant", "content": assistant_reply})

    if action == "end":
        # Summarize the conversation and log it, then end the call politely
        summarize_call(call_sid, from_number)

        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="Polly.Joanna">{assistant_reply}</Say>
  <Say voice="Polly.Joanna">Thank you for calling. Have a great day.</Say>
  <Hangup/>
</Response>
"""
        return Response(twiml, mimetype="text/xml")

    # Otherwise, continue conversation with another Gather
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Gather input="speech"
          action="/handle_input"
          method="POST"
          speechTimeout="auto">
    <Say voice="Polly.Joanna">{assistant_reply}</Say>
  </Gather>
  <Say voice="Polly.Joanna">If you are still there, please speak after the beep.</Say>
</Response>
"""
    return Response(twiml, mimetype="text/xml")


def summarize_call(call_sid: str, from_number: str):
    """
    After the call, ask OpenAI to summarize everything in a structured way.
    Save this to a text file. Later we can send to email, CRM, etc.
    """
    conv = CALL_CONVERSATIONS.get(call_sid)
    if not conv:
        return

    messages = conv["messages"] + [
        {
            "role": "user",
            "content": f"""
Please summarize this call in a JSON object with keys:
- caller_number
- name
- issue_or_request
- address_or_city
- preferred_time
- urgency_level ("low", "medium", "high")
- summary
- recommendation_for_business (what the business should do next)

Use "{from_number}" as caller_number. 
If information is missing, use empty strings.
"""
        }
    ]

    summary_text = call_openai(messages)

    # Create logs folder if not exists
    os.makedirs("logs", exist_ok=True)

    timestamp = datetime.utcnow().isoformat()
    log_line = f"\n\n=== CALL {call_sid} at {timestamp} UTC ===\n{summary_text}\n"

    # Save to logs/call_summaries.txt
    with open("logs/call_summaries.txt", "a", encoding="utf-8") as f:
        f.write(log_line)

    # Also print to server logs (Render logs)
    print(log_line)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

