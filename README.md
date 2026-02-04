# 🍯 Agentic Honeypot API

A production-ready REST API that detects scam messages and autonomously engages scammers to extract intelligence using Claude AI.

## Features

- 🔍 **Scam Detection**: Analyzes messages for scam patterns using keyword analysis, urgency detection, impersonation detection, and threat identification
- 🤖 **AI Agent**: Human-like responses using Claude AI with a realistic "slightly naive but cautious" persona
- 📊 **Intelligence Extraction**: Extracts bank accounts, UPI IDs, phone numbers, phishing URLs, and suspicious keywords
- 📝 **Session Management**: Tracks conversations per session with persistent intelligence accumulation
- 📡 **Automatic Callback**: Posts results to hackathon API when sufficient engagement is reached (8-15 messages or key intelligence extracted)

## Quick Start

### 1. Install Dependencies

```bash
cd d:\honeypot
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example environment file and update with your keys:

```bash
copy .env.example .env
```

Edit `.env`:
```env
API_KEY=your-secret-api-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
CALLBACK_URL=https://hackathon.guvi.in/api/updateHoneyPotFinalResult
LOG_LEVEL=INFO
```

### 3. Run the Server

```bash
python run.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### POST /api/scam-detection

Main endpoint for processing scam messages.

**Headers:**
- `x-api-key`: Your API key (required)
- `Content-Type`: application/json

**Request Body:**
```json
{
  "sessionId": "session-123",
  "message": {
    "sender": "scammer",
    "text": "Dear customer, your SBI account has been blocked. Share OTP to verify.",
    "timestamp": "2026-02-04T16:50:00Z"
  },
  "conversationHistory": [],
  "metadata": {
    "channel": "sms",
    "language": "en",
    "locale": "en-IN"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "reply": "What? My account has problem? But I just checked balance yesterday!"
}
```

### GET /api/session/{session_id}

Get current session information (for debugging).

### POST /api/trigger-callback/{session_id}

Manually trigger the final callback for a session.

### GET /health

Health check endpoint.

## Example Test Scenarios

### Bank Suspension Scam
```bash
curl -X POST http://localhost:8000/api/scam-detection \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-api-key" \
  -d '{
    "sessionId": "test-bank-1",
    "message": {
      "sender": "scammer",
      "text": "URGENT: Your HDFC Bank account will be blocked in 24 hours. Call +91 9876543210 immediately to verify.",
      "timestamp": "2026-02-04T17:00:00Z"
    },
    "conversationHistory": [],
    "metadata": {"channel": "sms", "language": "en", "locale": "en-IN"}
  }'
```

### UPI Scam
```bash
curl -X POST http://localhost:8000/api/scam-detection \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-api-key" \
  -d '{
    "sessionId": "test-upi-1",
    "message": {
      "sender": "scammer",
      "text": "Congratulations! You won Rs.50,000 lottery. Send Rs.500 to verify@paytm to claim your prize.",
      "timestamp": "2026-02-04T17:00:00Z"
    },
    "conversationHistory": [],
    "metadata": {"channel": "whatsapp", "language": "en", "locale": "en-IN"}
  }'
```

## Final Callback Payload

When sufficient engagement is reached, the API automatically POSTs to the hackathon callback URL:

```json
{
  "sessionId": "session-123",
  "scamDetected": true,
  "totalMessagesExchanged": 12,
  "extractedIntelligence": {
    "bankAccounts": ["1234567890123456"],
    "upiIds": ["scammer@paytm"],
    "phishingLinks": ["https://fake-bank.com/verify"],
    "phoneNumbers": ["+91 9876543210"],
    "suspiciousKeywords": ["urgent", "blocked", "verify", "otp"]
  },
  "agentNotes": "Detected tactics: Bank: HDFC, urgency_tactics, threat_detected. Scam confidence score: 85/100. Extracted: 1 bank account(s), 1 UPI ID(s), 1 phone number(s). Engaged over 12 messages from 2026-02-04 11:30 UTC"
}
```

## Deployment

### Render

1. Create a new Web Service from your Git repository
2. Build Command: `pip install -r requirements.txt`
3. Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add environment variables in the dashboard

### Railway

1. Connect your GitHub repository
2. Railway auto-detects Python application
3. Add environment variables
4. Deploy!

### Docker (Optional)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Project Structure

```
honeypot/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration
│   ├── models.py            # Pydantic models
│   ├── auth.py              # API key authentication
│   ├── routers/
│   │   └── scam_detection.py
│   ├── services/
│   │   ├── scam_detector.py
│   │   ├── intelligence_extractor.py
│   │   ├── ai_agent.py
│   │   ├── session_manager.py
│   │   └── callback_service.py
│   └── utils/
│       ├── patterns.py
│       └── logger.py
├── requirements.txt
├── .env.example
├── run.py
└── README.md
```

## Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `API_KEY` | API key for authentication | `honeypot-secret-key` |
| `ANTHROPIC_API_KEY` | Claude AI API key | - |
| `CALLBACK_URL` | Hackathon callback URL | `https://hackathon.guvi.in/api/updateHoneyPotFinalResult` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |

## License

MIT License - Built for the Hackathon 2026
