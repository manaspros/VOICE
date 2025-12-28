# Quick Start Guide - Twilio Voice AI Assistant

## 5-Minute Setup

### 1. Install Dependencies (1 minute)

```bash
# Run the setup script
./setup.sh

# Or manually:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment (1 minute)

Edit `.env`:
```bash
cp .env.example .env
nano .env  # or use your favorite editor
```

Add your Twilio credentials:
```
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
```

### 3. Start ngrok (30 seconds)

```bash
# In a new terminal
ngrok http 8000
```

Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`) and update `.env`:
```
PUBLIC_URL=https://abc123.ngrok.io
```

### 4. Start Server (30 seconds)

```bash
python app.py
```

You should see:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 5. Configure Twilio Number (2 minutes)

1. Go to: https://console.twilio.com/us1/develop/phone-numbers/manage/incoming
2. Click your phone number
3. Scroll to "Voice Configuration"
4. Set:
   - **A Call Comes In**: Webhook
   - **URL**: `https://your-ngrok-url.ngrok.io/voice/incoming`
   - **HTTP**: POST
5. Click **Save**

## Test It!

### Option 1: Call Your Twilio Number

1. Call your Twilio number from any phone
2. Listen to the greeting
3. Speak something
4. Wait 4 seconds
5. The system will respond

### Option 2: Make an Outbound Call

```bash
# Using curl
curl -X POST "http://localhost:8000/make-call?to_number=%2B1234567890"

# Using Python
python examples.py
```

## What Happens During a Call

```
1. Call starts
   ↓
2. Greeting plays: "Hello! I'm your AI assistant..."
   ↓
3. Audio streaming begins (WebSocket connects)
   ↓
4. You speak...
   ↓
5. System detects 4 seconds of silence
   ↓
6. Audio is processed:
   - Speech-to-Text (STT)
   - AI generates response
   - Text-to-Speech (TTS)
   ↓
7. Response plays back to you
   ↓
8. Loop continues...
```

## Check Logs

```bash
# Server logs
tail -f logs/app.log

# Or watch in real-time
python app.py
```

## Troubleshooting

### "Connection refused"
- Make sure FastAPI server is running: `python app.py`
- Check the port is 8000

### "WebSocket connection failed"
- Verify ngrok is running
- Check PUBLIC_URL in `.env` matches ngrok URL
- Use `wss://` (not `ws://`) for production

### "No audio received"
- Check Twilio webhook configuration
- Verify URL includes `/voice/incoming`
- Check server logs for errors

### "Call connects but no response"
- Audio processing functions are placeholders
- Implement STT/AI/TTS integrations (see README_VOICE.md)

## Next Steps

1. **Integrate Speech-to-Text**: Add OpenAI Whisper, Google Cloud STT, etc.
2. **Add AI Processing**: Connect to GPT-4, Claude, or local LLM
3. **Implement TTS**: Use MeloTTS (already in project!) or other services
4. **Add Database**: Store call logs and transcriptions
5. **Deploy to Production**: AWS, Heroku, or DigitalOcean

## Useful Commands

```bash
# Start everything
./setup.sh                    # First time only
source venv/bin/activate      # Activate venv
python app.py                 # Start server

# In separate terminals
ngrok http 8000               # Expose locally

# Make test calls
python examples.py            # Interactive examples
curl -X POST "http://localhost:8000/make-call?to_number=%2B1234567890"

# Check health
curl http://localhost:8000/

# Interrupt a call
curl -X POST "http://localhost:8000/interrupt-call/CAxxxx"
```

## Architecture at a Glance

```
┌─────────┐     ┌─────────┐     ┌──────────────┐
│  Phone  │────▶│ Twilio  │────▶│ FastAPI      │
│         │     │         │     │ + WebSocket  │
└─────────┘     └─────────┘     └──────────────┘
                                        │
                                        ▼
                                ┌──────────────┐
                                │ Audio Buffer │
                                │ (4s silence) │
                                └──────────────┘
                                        │
                                        ▼
                     ┌──────────────────────────────┐
                     │                              │
                     ▼                              ▼
              ┌───────────┐                  ┌──────────┐
              │    STT    │──────▶AI◀────────│   TTS    │
              └───────────┘                  └──────────┘
                     │                              │
                     └──────────────┬───────────────┘
                                    ▼
                             ┌─────────────┐
                             │ Play Audio  │
                             │  on Call    │
                             └─────────────┘
```

## Support

- Check `README_VOICE.md` for detailed documentation
- Review `examples.py` for code samples
- See Twilio docs: https://www.twilio.com/docs/voice

Happy building! 🎉
