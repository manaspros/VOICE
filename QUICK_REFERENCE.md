# Twilio Outbound Calling - Quick Reference

## 🚀 Quick Start

```bash
# 1. Start server
python app.py

# 2. Make a test call
python test_call.py +1234567890

# 3. Or test locally (no phone call)
python test_local.py

# 4. View demo
python demo_conversation.py
```

## 📞 API Endpoints

### Make an Outbound Call
```bash
POST /make-call
Content-Type: application/json

{
  "to_number": "+1234567890",
  "from_number": "+0987654321",  // Optional
  "initial_message": "Custom greeting"  // Optional
}
```

### Monitor Sessions
```bash
GET /sessions           # List all active calls
GET /session/{call_sid} # Get specific call details
GET /                   # Server health check
```

### TwiML Endpoints (Twilio webhooks)
```bash
POST /voice/outbound      # Initial greeting for outbound calls
POST /voice/incoming      # Handle inbound calls
POST /voice/process-speech # Process user speech input
POST /call-status         # Call status updates
```

## 🎤 Conversation Commands

Users can say:
- **"What time is it?"** → Get current time
- **"What's the date?"** → Get current date
- **"Hello" / "Hi"** → Greeting response
- **"Help"** → General help information
- **"Thank you" / "Goodbye"** → End call gracefully

## 🔧 Configuration

### Required Environment Variables
```env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxx...
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
PUBLIC_URL=https://your-domain.ngrok.io
```

### Optional Settings
```env
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
SILENCE_THRESHOLD_SECONDS=4.0
```

## 🎯 Phone Number Format

Always use **E.164 format**:
- ✅ Correct: `+14155551234`
- ❌ Wrong: `(415) 555-1234`
- ❌ Wrong: `14155551234`

## 📊 Response Structure

### Successful Call
```json
{
  "success": true,
  "call_sid": "CA1234567890abcdef",
  "status": "queued",
  "to": "+1234567890",
  "from": "+0987654321"
}
```

### Session Info
```json
{
  "active_sessions": 1,
  "sessions": {
    "CA123...": {
      "to": "+1234567890",
      "from": "+0987654321",
      "started_at": "2024-12-14T15:30:00",
      "message_count": 4
    }
  }
}
```

## 🐛 Common Issues

| Issue | Solution |
|-------|----------|
| "Number not verified" | Verify number in Twilio Console (trial account) |
| Call ends immediately | Check PUBLIC_URL is correct and accessible |
| No speech recognition | Speak clearly; check microphone permissions |
| "This is a trial account" | Normal for trial; upgrade for production |
| Webhook errors | Ensure ngrok is running; check server logs |

## 📝 Testing Workflow

1. **Local Testing** (no phone calls):
   ```bash
   python test_local.py
   ```

2. **Start ngrok** (for webhooks):
   ```bash
   ngrok http 8000
   # Update PUBLIC_URL in .env with ngrok URL
   ```

3. **Real Call Test**:
   ```bash
   python test_call.py +1234567890
   ```

4. **Monitor**:
   ```bash
   curl http://localhost:8000/sessions
   ```

## 🎓 Architecture Overview

```
Make Call → Twilio Dials → Call Answered
    ↓
Initial Greeting (TwiML Say)
    ↓
Listen for Speech (TwiML Gather)
    ↓
Transcribe Speech → Process → Generate Response
    ↓
Speak Response (TwiML Say)
    ↓
Listen Again (Loop) → Continue or End
```

## 🔐 Trial Account Limits

- ✅ Can call verified numbers only
- ✅ Plays "trial account" message
- ✅ Limited concurrent calls
- ✅ Sufficient for testing

**Upgrade to paid account for production!**

## 📚 Documentation Files

- `OUTBOUND_CALLING.md` - Comprehensive guide
- `README_VOICE.md` - Main project README
- `IMPLEMENTATION_CHANGES.md` - What was changed
- `demo_conversation.py` - Interactive demo

## 🆘 Quick Troubleshooting

```bash
# Check server status
curl http://localhost:8000/

# Test TwiML endpoint
curl -X POST http://localhost:8000/voice/outbound

# View server logs
tail -f logs/app.log

# Check ngrok status
curl http://127.0.0.1:4040/api/tunnels
```

## 💡 Pro Tips

1. **Always verify numbers** on trial accounts first
2. **Use test_local.py** before making real calls
3. **Monitor /sessions** during calls for debugging
4. **Keep ngrok running** when testing webhooks
5. **Upgrade account** for production deployment

## 🚀 Next Steps

1. Customize responses in `generate_ai_response_sync()`
2. Integrate LLM (OpenAI, Claude)
3. Add MeloTTS for natural voices
4. Deploy to production server
5. Set up call analytics

---

**Quick Help**: For detailed troubleshooting, see `OUTBOUND_CALLING.md`
**Demo**: Run `python demo_conversation.py` to see how it works
**Test**: Run `python test_local.py` to test without phone calls
