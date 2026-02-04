from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import re
import openai
from datetime import datetime
import httpx

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
PHONE_REGEX = r"\+91[0-9]{10}|\b[0-9]{10}\b"

# ================= UTIL =================

def extract(text):
    return {
        "bankAccounts": list(set(re.findall(BANK_REGEX, text))),
        "upiIds": list(set(re.findall(UPI_REGEX, text))),
        "phishingLinks": list(set(re.findall(URL_REGEX, text))),
        "phoneNumbers": list(set(re.findall(PHONE_REGEX, text))),
        "suspiciousKeywords": [k for k in ["urgent", "verify", "pan", "kyc", "block", "suspend", "otp", "account"] if k in text.lower()]
    }

# ================= ROOT =================

@app.head("/")
@app.get("/")
def ping():
    return {"status": "ready"}


@app.post("/")
async def honeypot(request: Request, x_api_key: str = Header(None)):
    
    # Authentication
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        body = await request.json()
    except Exception:
        body = {}

    # Quick response for empty test requests
    if not body or not body.get("message"):
        return {
            "status": "success",
            "reply": "Ready to detect scams"
        }

    # Parse request according to hackathon format
    session_id = body.get("sessionId", "default")
    
    # Extract message text from nested structure
    message_obj = body.get("message", {})
    if isinstance(message_obj, dict):
        message_text = message_obj.get("text", "")
    else:
        message_text = str(message_obj)
    
    # Get conversation history
    conversation_history = body.get("conversationHistory", [])

    # Initialize session if new
    if session_id not in sessions:
        sessions[session_id] = {
            "history": [],
            "turns": 0,
            "intel": {
                "bankAccounts": [],
                "upiIds": [],
                "phishingLinks": [],
                "phoneNumbers": [],
                "suspiciousKeywords": []
            }
        }

    session = sessions[session_id]

    # Add scammer message to history
    session["history"].append({"role": "user", "content": message_text})

    # ================= SCAM DETECTION =================

    scam_detected = False
    if client:
        try:
            detect_prompt = f"Reply only YES or NO. Is this a scam message?\n\nMessage:\n{message_text}"
            detect = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": detect_prompt}]
            )
            scam_detected = "yes" in detect.choices[0].message.content.lower()
        except Exception as e:
            print(f"OpenAI Error: {e}")
            scam_detected = True  # Fail safe
    else:
        # Simple keyword fallback
        scam_detected = any(k in message_text.lower() for k in ["urgent", "verify", "pan", "kyc", "block", "suspend", "otp", "account"])

    reply = "Okay."

    # ================= AGENT =================

    if scam_detected:
        agent_prompt = """You are an Indian person.
You believe the scammer.
Be polite and slow.
Try to get UPI ID, bank account, or payment link.
Never reveal scam detection.
Ask natural questions.
Keep responses short and simple."""
        
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
                reply = "Why is this happening? What should I do?"
        else:
            # Fallback responses
            replies = [
                "Why is my account being suspended?",
                "What do I need to do?",
                "Is this urgent?",
                "How can I fix this?"
            ]
            reply = replies[session["turns"] % len(replies)]

        session["history"].append({"role": "assistant", "content": reply})
        session["turns"] += 1

        # Extract intelligence
        intel = extract(message_text + " " + reply)
        for k in intel:
            session["intel"][k].extend(intel[k])
            session["intel"][k] = list(set(session["intel"][k]))

        # ================= FINAL CALLBACK =================
        # Send callback after sufficient engagement (8+ turns)
        if session["turns"] >= 8:
            try:
                callback_payload = {
                    "sessionId": session_id,
                    "scamDetected": True,
                    "totalMessagesExchanged": session["turns"],
                    "extractedIntelligence": session["intel"],
                    "agentNotes": f"Scammer engaged for {session['turns']} turns. Intelligence extracted."
                }
                
                async with httpx.AsyncClient() as http_client:
                    await http_client.post(
                        "https://hackathon.guvi.in/api/updateHoneyPotFinalResult",
                        json=callback_payload,
                        timeout=5
                    )
                print(f"✅ Final callback sent for session {session_id}")
            except Exception as e:
                print(f"❌ Callback failed: {e}")

    # ================= RESPONSE (HACKATHON FORMAT) =================
    
    return {
        "status": "success",
        "reply": reply
    }

# ================= HEALTH =================

@app.get("/health")
def health():
    return {"status": "healthy"}
