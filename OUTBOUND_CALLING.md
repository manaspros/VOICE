# Outbound Calling Guide

This guide explains how to properly implement and test outbound calling with the Twilio Voice AI Assistant.

## 🎯 Overview

The outbound calling system now uses **TwiML Gather** to capture speech input from the caller, making it compatible with Twilio trial accounts and providing a more reliable conversation flow.

## 🔧 Key Changes Made

### 1. **Replaced Media Streams with TwiML Gather**
   - **Before**: Used WebSocket streaming (requires verified numbers on trial accounts)
   - **After**: Uses `<Gather input="speech">` which works with trial accounts
   - **Benefit**: More reliable, works with unverified numbers

### 2. **Added Conversation State Management**
   - Tracks conversation history per call
   - Maintains context across multiple exchanges
   - Stores user and assistant messages

### 3. **Improved Speech Processing**
   - Uses Twilio's built-in speech recognition
   - Automatic silence detection
   - Confidence scoring for transcriptions

### 4. **Added Answering Machine Detection**
   - Detects when calls are answered by machines
   - Configurable via `machine_detection` parameter
   - Allows different handling for voicemail

## 📋 Prerequisites

1. **Twilio Account Setup**
   ```bash
   # Set environment variables
   export TWILIO_ACCOUNT_SID="your_account_sid"
   export TWILIO_AUTH_TOKEN="your_auth_token"
   export TWILIO_PHONE_NUMBER="+1234567890"
   ```

2. **Public URL (for webhooks)**
   - Use ngrok or similar tunneling service
   ```bash
   ngrok http 8000
   ```
   - Update `.env` with your public URL:
   ```
   PUBLIC_URL=https://your-subdomain.ngrok.io
   ```

3. **Phone Number Requirements**
   - **Trial Accounts**: Must verify numbers you want to call
   - **Paid Accounts**: Can call any number
   - All numbers must be in E.164 format: `+1234567890`

## 🚀 How to Make an Outbound Call

### Method 1: Using the Test Script

```bash
# Call a specific number
python test_call.py +1234567890

# Or edit TO_NUMBER in test_call.py and run
python test_call.py
```

### Method 2: Using curl

```bash
curl -X POST http://localhost:8000/make-call \
  -H "Content-Type: application/json" \
  -d '{
    "to_number": "+1234567890",
    "from_number": "+0987654321"
  }'
```

### Method 3: Using Python requests

```python
import requests

response = requests.post(
    "http://localhost:8000/make-call",
    json={
        "to_number": "+1234567890",
        "from_number": "+0987654321",  # Optional
        "initial_message": "Custom greeting"  # Optional
    }
)

print(response.json())
```

## 🎤 Call Flow

1. **Initiation**
   - API receives call request
   - Twilio places the call
   - Call SID is generated and tracked

2. **Answer**
   - Call is answered (by human or machine)
   - AI assistant speaks greeting: *"Hello! I'm your AI assistant. How can I help you today?"*

3. **Listen & Gather**
   - System waits for user speech
   - Uses TwiML `<Gather>` with `input="speech"`
   - Automatic silence detection (configurable timeout)

4. **Process Speech**
   - Speech is transcribed by Twilio
   - Transcription sent to `/voice/process-speech`
   - AI generates contextual response

5. **Respond**
   - AI response is spoken using Text-to-Speech
   - Conversation history is maintained
   - System waits for more input

6. **Continue or End**
   - Loop continues until user says goodbye
   - Or user hangs up
   - Or timeout occurs

## 🗣️ Testing the Conversation

### Example Interactions

**Test 1: Time Query**
```
Assistant: "Hello! I'm your AI assistant. How can I help you today?"
You: "What time is it?"
Assistant: "The current time is 3:45 PM."
You: "Thank you"
Assistant: "Thank you for calling. Have a great day! Goodbye."
```

**Test 2: Help Request**
```
Assistant: "Hello! I'm your AI assistant. How can I help you today?"
You: "I need help"
Assistant: "I can help you with information, answer questions, or assist with your needs. What would you like to know?"
You: "What's today's date?"
Assistant: "Today is Saturday, December 14, 2024."
```

**Test 3: Greeting**
```
Assistant: "Hello! I'm your AI assistant. How can I help you today?"
You: "Hello"
Assistant: "Hello! How can I assist you today?"
```

## 📊 Monitoring Calls

### Check Server Status
```bash
curl http://localhost:8000/
```

Response:
```json
{
  "status": "ok",
  "message": "Twilio Voice AI Assistant is running",
  "active_sessions": 2,
  "public_url": "https://your-subdomain.ngrok.io"
}
```

### View Active Sessions
```bash
curl http://localhost:8000/sessions
```

Response:
```json
{
  "active_sessions": 1,
  "sessions": {
    "CA1234567890abcdef": {
      "to": "+1234567890",
      "from": "+0987654321",
      "started_at": "2024-12-14T15:30:00",
      "message_count": 4
    }
  }
}
```

### Get Specific Call Details
```bash
curl http://localhost:8000/session/CA1234567890abcdef
```

Response includes full conversation history:
```json
{
  "to": "+1234567890",
  "from": "+0987654321",
  "conversation_history": [
    {
      "role": "user",
      "content": "What time is it?",
      "timestamp": "2024-12-14T15:30:15",
      "confidence": 0.95
    },
    {
      "role": "assistant",
      "content": "The current time is 3:30 PM.",
      "timestamp": "2024-12-14T15:30:16"
    }
  ],
  "started_at": "2024-12-14T15:30:00"
}
```

## 🐛 Troubleshooting

### Issue: "This is a trial account" message

**Problem**: Twilio announces trial account status before connecting

**Solutions**:
1. **For Testing**: This is normal for trial accounts
2. **For Production**: Upgrade to paid account
3. **Workaround**: Add delay or use paid account

### Issue: Call ends immediately after greeting

**Problem**: No TwiML endpoint or incorrect URL

**Check**:
```bash
# Verify your PUBLIC_URL is correct
echo $PUBLIC_URL

# Test webhook endpoint
curl https://your-subdomain.ngrok.io/voice/outbound
```

**Fix**:
- Ensure ngrok is running
- Update `.env` with correct PUBLIC_URL
- Restart the server

### Issue: "Number not verified"

**Problem**: Trying to call unverified number on trial account

**Solutions**:
1. Verify the number in Twilio Console
2. Upgrade to paid account
3. Use a verified number for testing

### Issue: No speech recognition

**Problem**: Speech input not being captured

**Check**:
- Speak clearly and loudly
- Check `speech_timeout` setting (default: "auto")
- Verify microphone permissions

**Debug**:
```bash
# Check logs for speech events
tail -f logs/app.log | grep "Speech from"
```

### Issue: Conversation doesn't continue

**Problem**: After AI responds, call hangs up

**Check**:
- Ensure `/voice/process-speech` endpoint is working
- Verify `<Gather>` is being returned in TwiML
- Check for errors in server logs

## 🔐 Trial Account Limitations

Twilio trial accounts have restrictions:

1. **Verified Numbers Only**: Can only call verified numbers
2. **Trial Message**: Plays announcement before connecting
3. **Limited Credits**: Monitor usage carefully
4. **Rate Limits**: Fewer concurrent calls

**To Verify a Number**:
1. Go to Twilio Console
2. Navigate to Phone Numbers > Verified Caller IDs
3. Click "+" to add new number
4. Enter number and verify via call or SMS

## 📝 Configuration Options

### Environment Variables

```bash
# Required
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
PUBLIC_URL=https://your-subdomain.ngrok.io

# Optional
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
SILENCE_THRESHOLD_SECONDS=4.0
```

### Call Parameters

When making a call, you can customize:

```python
{
  "to_number": "+1234567890",      # Required: E.164 format
  "from_number": "+0987654321",    # Optional: defaults to env
  "initial_message": "Custom text" # Optional: custom greeting
}
```

### TwiML Gather Settings

In `app.py`, you can adjust:

```python
gather = response.gather(
    input="speech",           # Input type: speech, dtmf, or both
    action="/process-speech", # Where to send results
    speech_timeout="auto",    # Silence detection: auto or seconds
    language="en-US",         # Recognition language
    hints="help, support"     # Expected words (improves accuracy)
)
```

## 🔧 Advanced Customization

### Add Custom Voice

Change the TTS voice in responses:

```python
response.say(
    "Your message",
    voice="Polly.Matthew",  # Male voice
    language="en-US"
)
```

Available voices: Polly.Joanna (female), Polly.Matthew (male), and others.

### Add Multiple Languages

```python
response.say(
    "Hola, ¿cómo puedo ayudarte?",
    voice="Polly.Conchita",
    language="es-ES"
)

gather = response.gather(
    input="speech",
    language="es-ES"  # Spanish recognition
)
```

### Integrate with LLM

Replace `generate_ai_response_sync()` with OpenAI:

```python
async def generate_ai_response_sync(user_input: str, call_sid: str) -> str:
    import openai
    
    # Get conversation history
    history = active_sessions[call_sid]["conversation_history"]
    
    # Format for OpenAI
    messages = [
        {"role": "system", "content": "You are a helpful phone assistant."}
    ]
    messages.extend([
        {"role": msg["role"], "content": msg["content"]}
        for msg in history
    ])
    messages.append({"role": "user", "content": user_input})
    
    # Get response
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages,
        max_tokens=100
    )
    
    return response.choices[0].message.content
```

## 📚 Next Steps

1. **Test Basic Calling**: Use test script with verified number
2. **Customize Responses**: Update `generate_ai_response_sync()`
3. **Integrate LLM**: Add OpenAI, Claude, or local LLM
4. **Add TTS**: Integrate MeloTTS for natural voices
5. **Deploy**: Move to production with paid Twilio account

## 🆘 Support

If you encounter issues:

1. Check server logs: `tail -f logs/app.log`
2. Verify Twilio configuration in Console
3. Test webhook URLs with curl
4. Review this guide's troubleshooting section

For more help, refer to:
- [Twilio Voice Documentation](https://www.twilio.com/docs/voice)
- [TwiML Reference](https://www.twilio.com/docs/voice/twiml)
- [Gather Verb Documentation](https://www.twilio.com/docs/voice/twiml/gather)
