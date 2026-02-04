from fastapi import FastAPI, Request, Header
from fastapi.middleware.cors import CORSMiddleware
import os
import re
import openai
from datetime import datetime

# ================= CONFIG =================

API_KEY = os.getenv("HONEYPOT_API_KEY", "my-honeypot-key")

# Initialize OpenAI Client (v1.x) - ONLY if key exists
openai_key = os.getenv("OPENAI_API_KEY")
if openai_key:
    client = openai.OpenAI(api_key=openai_key)
else:
    client = None  # No OpenAI - use fallback mode

# ================= APP =================

app = FastAPI(title="Agentic Honeypot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= MEMORY =================

sessions = {}

# ================= REGEX =================

UPI_REGEX = r"[a-zA-Z0-9.\-_]{2,}@[a-zA-Z]{2,}"
BANK_REGEX = r"\b\d{9,18}\b"
URL_REGEX = r"https?://\S+"

# ================= UTIL =================

def extract(text):
    return {
        "upi_ids": list(set(re.findall(UPI_REGEX, text))),
        "bank_accounts": list(set(re.findall(BANK_REGEX, text))),
        "phishing_urls": list(set(re.findall(URL_REGEX, text)))
    }

# ================= ROOT =================

@app.head("/")
@app.get("/")
def ping():
    return {
        "status": "ready",
        "service": "Agentic Honeypot API",
        "version": "1.0",
        "endpoints": {
            "scam_detection": "POST /",
            "health": "GET /health"
        },
        "authentication": "x-api-key header required for POST requests"
    }

@app.post("/")
async def honeypot(request: Request, x_api_key: str = Header(None)):

    if x_api_key != API_KEY:
        return {"error": "unauthorized"}

    try:
        body = await request.json()
    except Exception:
        body = {}

    session_id = body.get("conversation_id") or body.get("session_id") or "default"
    # Handle message being a dict or string
    msg_raw = body.get("message") or body.get("content") or ""
    if isinstance(msg_raw, dict):
        message = msg_raw.get("text") or msg_raw.get("content") or ""
    else:
        message = str(msg_raw)

    if session_id not in sessions:
        sessions[session_id] = {
            "history": [],
            "turns": 0,
            "intel": {
                "upi_ids": [],
                "bank_accounts": [],
                "phishing_urls": []
            }
        }

    session = sessions[session_id]

    session["history"].append({"role": "user", "content": message})

    # ================= SCAM DETECTION =================

    detect_prompt = f"""
Reply only YES or NO.
Is this a scam message?

Message:
{message}
"""
    
    # Use Fallback if no OpenAI Key
    scam_detected = False
    if client:
        try:
            detect = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": detect_prompt}]
            )
            scam_detected = "yes" in detect.choices[0].message.content.lower()
        except Exception as e:
            print(f"OpenAI Error: {e}")
            scam_detected = True # Fail safe
    else:
        # Simple keyword fallback
        scam_detected = any(k in message.lower() for k in ["urgent", "verify", "pan", "kyc", "block", "suspend"])

    reply = "Okay."

    # ================= AGENT =================

    if scam_detected:

        agent_prompt = """
You are an Indian person.
You believe the scammer.
Be polite and slow.
Try to get UPI ID, bank account, or payment link.
Never reveal scam detection.
Ask natural questions.
"""
        
        if client:
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": agent_prompt},
                        *session["history"]
                    ]
                )
                reply = response.choices[0].message.content
            except Exception:
                reply = "Okay sure, please tell me what to do?"
        else:
            reply = "I am worried. Please help me fix this."

        session["history"].append({"role": "assistant", "content": reply})
        session["turns"] += 1

        intel = extract(message + " " + reply)

        for k in intel:
            session["intel"][k].extend(intel[k])
            session["intel"][k] = list(set(session["intel"][k]))

    # ================= RESPONSE =================

    return {
        "status": "success",
        "timestamp": datetime.utcnow().isoformat(),
        "session_id": session_id,
        "scam_detected": scam_detected,
        "agent_active": scam_detected,
        "engagement_turns": session["turns"],
        "intelligence": session["intel"],
        "reply_to_scammer": reply
    }

# ================= HEALTH =================

@app.get("/health")
def health():
    return {"status": "healthy"}
