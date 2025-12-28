# Twilio Voice AI Assistant with FastAPI

A real-time voice AI assistant built with FastAPI, Twilio Voice, and WebSockets. This application handles voice calls, streams audio in real-time, detects silence, and generates AI-powered responses.

## ✨ Features

- 🎙️ **Real-time Audio Streaming**: Receive live audio from Twilio calls via WebSocket
- 📞 **Inbound & Outbound Calls**: Handle both incoming calls and make outbound calls
- 🗣️ **Speech Recognition**: Built-in speech-to-text using Twilio's Gather verb
- 💬 **Conversation Management**: Track and maintain conversation context
- 🤖 **AI Responses**: Generate contextual responses based on user input
- 🔇 **Silence Detection**: Automatically detect when caller stops speaking (configurable threshold)
- ⏸️ **Call Interruption**: Pause playback when caller starts speaking again
- 📊 **Session Monitoring**: Track active calls and conversation history
- 🔄 **WebSocket Updates**: Real-time updates on call status and audio processing

## 🆕 Latest Updates

### Outbound Calling Implementation
- ✅ Replaced WebSocket streaming with TwiML Gather for better compatibility
- ✅ Added conversation state management
- ✅ Implemented speech processing with confidence scoring
- ✅ Added answering machine detection
- ✅ Created comprehensive testing tools

**See [OUTBOUND_CALLING.md](./OUTBOUND_CALLING.md) for detailed guide on making outbound calls.**

## Architecture

```
┌─────────┐        ┌─────────┐        ┌──────────────┐
│  Caller │◄──────►│ Twilio  │◄──────►│   FastAPI    │
└─────────┘        └─────────┘        │    Server    │
                                       └──────┬───────┘
                                              │
                   ┌──────────────────────────┴───────────────────┐
                   │                                               │
            ┌──────▼───────┐                              ┌───────▼────────┐
            │   Speech     │                              │   Conversation │
            │ Recognition  │                              │    Manager     │
            └──────┬───────┘                              └───────┬────────┘
                   │                                               │
            ┌──────▼───────┐                              ┌───────▼────────┐
            │   AI Model   │                              │   Response     │
            │  (Optional)  │                              │   Generator    │
            └──────┬───────┘                              └───────┬────────┘
                   │                                               │
                   └───────────────────┬───────────────────────────┘
                                       │
                                ┌──────▼───────┐
                                │     TTS      │
                                │  (Twilio)    │
                                └──────────────┘
```

## Prerequisites

- Python 3.8+
- Twilio account with:
  - Account SID
  - Auth Token
  - Phone number with Voice capabilities
- ngrok (for local development) or a public server

## Installation

1. **Clone the repository**
```bash
cd /home/aryan/IMP/mellotts
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
cp .env.example .env
```

Edit `.env` and add your credentials:
```env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+1234567890
PUBLIC_URL=https://your-ngrok-subdomain.ngrok.io
```

## Quick Start

### 1. Start the FastAPI server

```bash
python app.py
```

The server will start on `http://localhost:8000`

### 2. Expose your local server with ngrok

In a new terminal:
```bash
ngrok http 8000
```

Copy the ngrok URL (e.g., `https://abc123.ngrok.io`) and update your `.env` file:
```env
PUBLIC_URL=https://abc123.ngrok.io
```

Restart the FastAPI server for changes to take effect.

### 3. Configure Twilio Phone Number (for inbound calls)

1. Go to [Twilio Console - Phone Numbers](https://console.twilio.com/us1/develop/phone-numbers/manage/incoming)
2. Click on your phone number
3. Under "Voice Configuration":
   - **A Call Comes In**: Webhook
   - **URL**: `https://your-ngrok-url.ngrok.io/voice/incoming`
   - **HTTP**: POST
4. Save

## 📞 Making Calls

### Method 1: Using the Test Script (Recommended)

```bash
# Make a call to a specific number
python test_call.py +1234567890
```

### Method 2: Using curl

```bash
curl -X POST "http://localhost:8000/make-call" \
  -H "Content-Type: application/json" \
  -d '{"to_number": "+1234567890"}'
```

### Method 3: Using Python

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
# Output: {"success": true, "call_sid": "CAxxxx...", "status": "queued"}
```

### Testing Locally (No Phone Call)

```bash
# Test the endpoints without making actual calls
python test_local.py
```

**📖 For comprehensive outbound calling guide, see [OUTBOUND_CALLING.md](./OUTBOUND_CALLING.md)**

## 🎤 Conversation Flow

When you make an outbound call:

1. **Call Initiated**: System dials the number
2. **Greeting**: "Hello! I'm your AI assistant. How can I help you today?"
3. **Listen**: System waits for your speech
4. **Process**: Your speech is transcribed and processed
5. **Respond**: AI generates and speaks a response
6. **Continue**: Loop continues until you say goodbye or hang up

### Example Conversation

```
🤖 Assistant: "Hello! I'm your AI assistant. How can I help you today?"
👤 You: "What time is it?"
🤖 Assistant: "The current time is 3:45 PM."
👤 You: "Thank you"
🤖 Assistant: "Thank you for calling. Have a great day! Goodbye."
```

## Receiving Inbound Calls

Simply call your Twilio phone number. The system will:
1. Answer the call
2. Say a greeting
3. Start streaming audio
4. Listen for speech
5. Detect 4-second silence
6. Process and respond

### Call Flow

1. **Caller speaks** → Audio buffered in real-time
2. **4 seconds of silence** → Audio processing triggered
3. **STT (Speech-to-Text)** → Transcribe the audio
4. **AI Processing** → Generate response
5. **TTS (Text-to-Speech)** → Convert to audio
6. **Play Response** → Send audio back to caller
7. **Repeat** → Listen for next input

### Interrupting Playback

When the caller starts speaking while AI is responding:

```bash
curl -X POST "http://localhost:8000/interrupt-call/CAxxxxxxxxxxxx"
```

## API Endpoints

### HTTP Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/voice/incoming` | POST | TwiML webhook for incoming calls |
| `/voice/outbound` | POST | TwiML for outbound calls |
| `/make-call` | POST | Initiate an outbound call |
| `/call-status` | POST | Receive call status updates |
| `/interrupt-call/{call_sid}` | POST | Pause current playback |

### WebSocket Endpoint

| Endpoint | Protocol | Description |
|----------|----------|-------------|
| `/media` | WebSocket | Receive real-time audio streams |

## Configuration

Edit `config.py` or `.env`:

```python
# Silence detection threshold (seconds)
SILENCE_THRESHOLD_SECONDS=4.0

# Audio settings
AUDIO_SAMPLE_RATE=8000  # Twilio uses 8kHz mulaw

# Server settings
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
```

## Integration Points

### 1. Speech-to-Text (STT)

Update `transcribe_audio()` in `app.py`:

```python
async def transcribe_audio(audio_data: bytes) -> str:
    # Example: OpenAI Whisper
    import openai
    
    # Save audio to temp file
    with open("temp.wav", "wb") as f:
        f.write(audio_data)
    
    # Transcribe
    with open("temp.wav", "rb") as f:
        transcript = openai.Audio.transcribe("whisper-1", f)
    
    return transcript["text"]
```

### 2. AI Response Generation

Update `generate_ai_response()` in `app.py`:

```python
async def generate_ai_response(transcription: str) -> str:
    # Example: OpenAI GPT
    import openai
    
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful voice assistant."},
            {"role": "user", "content": transcription}
        ]
    )
    
    return response.choices[0].message.content
```

### 3. Text-to-Speech (TTS) with MeloTTS

Update `generate_tts()` in `app.py`:

```python
async def generate_tts(text: str) -> str:
    from melo.api import TTS
    import uuid
    
    # Initialize MeloTTS
    model = TTS(language='EN', device='auto')
    speaker_ids = model.hps.data.spk2id
    
    # Generate audio
    output_path = f"output_{uuid.uuid4()}.wav"
    model.tts_to_file(text, speaker_ids['EN-US'], output_path, speed=1.0)
    
    # Upload to S3 or accessible URL
    public_url = upload_to_s3(output_path)  # Implement this
    
    return public_url
```

## Audio Buffer Details

The `AudioBuffer` class:
- Collects audio chunks in real-time
- Performs simple energy-based Voice Activity Detection (VAD)
- Tracks silence duration
- Triggers processing after 4 seconds of silence

```python
# Customize silence detection
audio_buffer = AudioBuffer(
    call_sid="CAxxxx",
    silence_threshold=4.0  # seconds
)
```

## Monitoring & Debugging

### Check Active Sessions
```python
# In your code
print(active_sessions)
```

### View Logs
```bash
tail -f logs/app.log
```

### Test WebSocket Connection
```bash
wscat -c ws://localhost:8000/media
```

## Production Deployment

### 1. Use a Production Server

Replace ngrok with:
- AWS EC2 + Elastic IP
- Heroku
- DigitalOcean
- Google Cloud Run

### 2. Add Security

```python
from fastapi import Header, HTTPException

async def verify_twilio_signature(
    request: Request,
    x_twilio_signature: str = Header(None)
):
    # Verify webhook is from Twilio
    from twilio.request_validator import RequestValidator
    
    validator = RequestValidator(settings.twilio_auth_token)
    url = str(request.url)
    params = await request.form()
    
    if not validator.validate(url, params, x_twilio_signature):
        raise HTTPException(status_code=403, detail="Invalid signature")
```

### 3. Add Database

Store call logs, transcriptions, and analytics:
```python
from sqlalchemy import create_engine, Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class CallLog(Base):
    __tablename__ = "call_logs"
    
    call_sid = Column(String, primary_key=True)
    transcription = Column(String)
    ai_response = Column(String)
    created_at = Column(DateTime)
```

### 4. Scale with Redis

For multiple servers, use Redis for session storage:
```python
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

# Store session
redis_client.setex(
    f"session:{call_sid}",
    3600,  # TTL
    json.dumps(session_data)
)
```

## Troubleshooting

### WebSocket connection fails
- Check ngrok is running
- Verify PUBLIC_URL in .env
- Ensure WebSocket path uses `wss://` in production

### No audio received
- Check Twilio phone number configuration
- Verify webhook URL is correct
- Check server logs for errors

### Silence detection not working
- Adjust `SILENCE_THRESHOLD_SECONDS`
- Implement proper VAD library
- Check audio energy threshold in `_is_silence()`

## Advanced Features

### Custom Parameters in Stream

```python
stream = Stream(url=f"wss://{settings.public_url.replace('https://', '')}/media")
stream.parameter(name="language", value="en-US")
stream.parameter(name="user_id", value="123")
```

### Bidirectional Audio

Send audio TO the call:
```python
# Send audio via WebSocket
media_message = {
    "event": "media",
    "streamSid": stream_sid,
    "media": {
        "payload": base64.b64encode(audio_bytes).decode('utf-8')
    }
}
await websocket.send_text(json.dumps(media_message))
```

## Contributing

Feel free to submit issues and enhancement requests!

## License

MIT License

## Resources

- [Twilio Voice API Docs](https://www.twilio.com/docs/voice)
- [Twilio Media Streams](https://www.twilio.com/docs/voice/media-streams)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [MeloTTS Repository](https://github.com/myshell-ai/MeloTTS)
