import base64
import json
import asyncio
import logging
import re
from datetime import datetime
from typing import Dict, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Response, HTTPException
from fastapi.responses import HTMLResponse
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Start, Stream, Dial, Say
from config import settings
import tempfile
import subprocess
import os
import chromadb
from redis.asyncio import Redis, ConnectionPool
from session import RedisSessionManager
from rag import RAGPipeline, RAGRetriever, GeminiGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Twilio Voice AI Assistant")

# Initialize Twilio client
twilio_client = Client(settings.twilio_account_sid, settings.twilio_auth_token)

# Initialize Redis connection pool
redis_pool = ConnectionPool(
    host=settings.redis_host,
    port=settings.redis_port,
    password=settings.redis_password,
    db=settings.redis_db,
    max_connections=100,
    decode_responses=True
)
redis_client = Redis(connection_pool=redis_pool)

# Initialize Redis session manager
session_manager = RedisSessionManager(redis_client, ttl=settings.session_ttl)

# Initialize Chroma and RAG pipeline (will be set in startup event)
chroma_client = None
rag_pipeline = None


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global chroma_client, rag_pipeline

    logger.info("Starting Twilio Voice AI Assistant...")

    # Test Redis connection
    try:
        await redis_client.ping()
        logger.info("✓ Redis connected")
    except Exception as e:
        logger.error(f"✗ Redis connection failed: {e}")
        logger.warning("Running without Redis - sessions will not persist")

    # Initialize Chroma and RAG pipeline
    try:
        if settings.gemini_api_key and settings.gemini_api_key != "your_gemini_api_key_here":
            chroma_client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
            retriever = RAGRetriever(chroma_client, settings.chroma_collection_name)
            generator = GeminiGenerator(settings.gemini_api_key, settings.gemini_model)
            rag_pipeline = RAGPipeline(retriever, generator)
            logger.info("✓ RAG pipeline initialized")
        else:
            logger.warning("✗ Gemini API key not configured - RAG disabled")
    except Exception as e:
        logger.error(f"✗ RAG initialization failed: {e}")
        logger.warning("Running without RAG - will use fallback responses")

    logger.info("✓ Twilio Voice AI Assistant ready")


def detect_language(text: str) -> str:
    """
    Detect if text is Hindi or English

    Args:
        text: Text to analyze

    Returns:
        Language code ('hi-IN' or 'en')
    """
    hindi_pattern = re.compile(r'[\u0900-\u097F]')
    return "hi-IN" if hindi_pattern.search(text) else "en"


async def download_recording_async(recording_url: str) -> bytes:
    """
    Download audio recording asynchronously

    Args:
        recording_url: URL of the recording

    Returns:
        Audio data as bytes
    """
    import aiohttp

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{recording_url}.mp3",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    logger.warning(f"Failed to download recording: status {response.status}")
                    return b""
    except Exception as e:
        logger.error(f"Error downloading recording: {e}")
        return b""


# class AudioBuffer:
#     """Buffers audio chunks and detects silence"""
    
#     def __init__(self, call_sid: str, silence_threshold: float = 4.0):
#         self.call_sid = call_sid
#         self.silence_threshold = silence_threshold
#         self.audio_chunks = []
#         self.last_audio_timestamp = None
#         self.is_speaking = False
#         self.silence_start_time = None
        
#     def add_chunk(self, audio_data: bytes, timestamp: float):
#         """Add audio chunk to buffer"""
#         self.audio_chunks.append(audio_data)
#         self.last_audio_timestamp = timestamp
        
#         # Detect speech (simple energy-based detection)
#         # In production, use a proper VAD (Voice Activity Detection) library
#         is_silent = self._is_silence(audio_data)
        
#         if not is_silent:
#             self.is_speaking = True
#             self.silence_start_time = None
#         elif self.is_speaking and is_silent:
#             if self.silence_start_time is None:
#                 self.silence_start_time = timestamp
                
#     def _is_silence(self, audio_data: bytes) -> bool:
#         """Basic silence detection based on audio energy"""
#         # Convert bytes to integers and calculate RMS energy
#         if len(audio_data) == 0:
#             return True
            
#         # Simple energy threshold (you may want to adjust this)
#         energy = sum(abs(b - 128) for b in audio_data) / len(audio_data)
#         return energy < 10  # Threshold for silence
        
#     def check_silence_duration(self, current_time: float) -> bool:
#         """Check if silence threshold has been reached"""
#         if self.silence_start_time is None:
#             return False
            
#         silence_duration = current_time - self.silence_start_time
#         return silence_duration >= self.silence_threshold
        
#     def get_buffered_audio(self) -> bytes:
#         """Get all buffered audio as bytes"""
#         return b''.join(self.audio_chunks)
        
#     def clear_buffer(self):
#         """Clear the audio buffer"""
#         self.audio_chunks = []
#         self.is_speaking = False
#         self.silence_start_time = None


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "Twilio Voice AI Assistant is running",
        "active_sessions": len(active_sessions),
        "public_url": settings.public_url
    }


@app.get("/sessions")
async def get_sessions():
    """Get active call sessions"""
    sessions = await session_manager.get_all_sessions()

    return {
        "active_sessions": len(sessions),
        "sessions": {
            call_sid: {
                "to": session.get("to"),
                "from": session.get("from"),
                "started_at": session.get("started_at"),
                "message_count": len(session.get("conversation_history", []))
            }
            for call_sid, session in sessions.items()
        }
    }


@app.get("/session/{call_sid}")
async def get_session(call_sid: str):
    """Get specific call session details"""
    session = await session_manager.get_session(call_sid)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return session


# @app.post("/voice/incoming")
# async def incoming_call(request: Request):
#     """Handle incoming calls - return TwiML to start streaming"""
#     form_data = await request.form()
#     call_sid = form_data.get("CallSid")
#     from_number = form_data.get("From")
    
#     logger.info(f"Incoming call from {from_number}, CallSid: {call_sid}")
    
#     # Create TwiML response with Stream
#     response = VoiceResponse()
#     # fetch custom intro from database or config if needed
#     response.say("Hello! I'm your AI assistant. What is your preference language?", voice="Polly.Joanna", language="en-US")
    
#     # Start streaming audio to our WebSocket
#     start = Start()
#     stream = Stream(url=f"wss://{settings.public_url.replace('https://', '')}/media")
#     stream.parameter(name="call_sid", value=call_sid)
#     start.append(stream)
#     response.append(start)
    
#     # Keep the call alive
#     response.pause(length=60)
    
#     return Response(content=str(response), media_type="application/xml")


@app.post("/voice/outbound")
async def outbound_call_twiml(request: Request):
    """TwiML for outbound calls - initial greeting"""
    form_data = await request.form()
    call_sid = form_data.get("CallSid")
    
    logger.info(f"Outbound call answered: {call_sid}")
    
    response = VoiceResponse()
    
    # Initial greeting
    response.say(
        "Hello! I'm your AI assistant. What is your preference language?",
        voice="Polly.Joanna",
        language="en-US"
    )
    
    # Use Gather to capture speech input
    gather = response.gather(
        input="speech",
        action=f"{settings.public_url}/voice/process-speech",
        method="POST",
        speech_timeout=3,  # Wait 3 seconds of silence before processing
        language="hi-IN",
        hints="help, information, question, support",
        speech_model="experimental_conversations",  # Better conversation model
        enhanced=True  # Enhanced speech recognition
    )
    
    # If no input is received
    response.say(
        "I didn't hear anything. Please try again or hang up.",
        voice="Polly.Joanna"
    )
    response.redirect(f"{settings.public_url}/voice/outbound")
    
    return Response(content=str(response), media_type="application/xml")


@app.post("/make-call")
async def make_call(request: Request):
    """
    Initiate an outbound call
    
    Request body:
        to_number: Phone number to call (E.164 format, e.g., +1234567890)
        from_number: Optional Twilio number to call from (defaults to configured number)
        initial_message: Optional custom greeting message
    """
    try:
        body = await request.json()
        to_number = body.get("to_number")
        from_number = body.get("from_number") or settings.twilio_phone_number
        initial_message = body.get("initial_message")
        
        if not to_number:
            raise HTTPException(status_code=400, detail="to_number is required")
        
        # Store initial message in session if provided
        session_data = {}
        if initial_message:
            session_data["initial_message"] = initial_message
            
        # Create call with TwiML URL
        call = twilio_client.calls.create(
            to=to_number,
            from_=from_number,
            url=f"{settings.public_url}/voice/outbound",
            status_callback=f"{settings.public_url}/call-status",
            status_callback_event=["initiated", "ringing", "answered", "completed"],
            machine_detection="DetectMessageEnd",  # Detect answering machines
            record=True
        )
        
        # Store session data
        await session_manager.create_session(call.sid, {
            "to": to_number,
            "from": from_number,
            "started_at": datetime.now().isoformat(),
            "language": "en",  # Default language
            **session_data
        })
        
        logger.info(f"Call initiated: {call.sid} to {to_number}")
        
        return {
            "success": True,
            "call_sid": call.sid,
            "status": call.status,
            "to": to_number,
            "from": from_number
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error making call: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/voice/process-speech")
async def process_speech(request: Request):
    """Process speech input from caller"""
    form_data = await request.form()
    call_sid = form_data.get("CallSid")
    speech_result = form_data.get("SpeechResult", "")
    confidence = form_data.get("Confidence", "0.0")
    recording_url = form_data.get("RecordingUrl", "")  # Audio file URL
    recording_sid = form_data.get("RecordingSid", "")  # Recording ID
    
    logger.info(f"Speech from {call_sid}: '{speech_result}' (confidence: {confidence})")
    logger.info(f"Recording URL: {recording_url}, SID: {recording_sid}")

    response = VoiceResponse()

    # Download recording asynchronously (non-blocking)
    if recording_url:
        audio_data = await download_recording_async(recording_url)
        if audio_data:
            # Store recording metadata in session
            await redis_client.hset(f"session:{call_sid}", "last_recording_url", recording_url)
            logger.debug(f"Downloaded and stored recording for {call_sid}")

    # Detect and store language
    detected_lang = detect_language(speech_result)
    await redis_client.hset(f"session:{call_sid}", "language", detected_lang)
    logger.debug(f"Detected language for {call_sid}: {detected_lang}")
    
    # Store user message in conversation history
    await session_manager.add_message(call_sid, {
        "role": "user",
        "content": speech_result,
        "timestamp": datetime.now().isoformat(),
        "confidence": float(confidence),
        "recording_url": recording_url,
        "recording_sid": recording_sid
    })
    
    # Generate AI response
    try:
        ai_response = await generate_ai_response_sync(speech_result, call_sid)

        # Store AI response in conversation history
        await session_manager.add_message(call_sid, {
            "role": "assistant",
            "content": ai_response,
            "timestamp": datetime.now().isoformat()
        })
        
        # Speak the response
        response.say(
            ai_response,
            voice="Polly.Aditi",
            # language="hi-IN"
        )
        
        # Wait for more input
        gather = response.gather(
            input="speech",
            action=f"{settings.public_url}/voice/process-speech",
            method="POST",
            speech_timeout=3,  # Wait 3 seconds of silence
            language="hi-IN",
            hints="help, information, question, support, goodbye, thanks",
            speech_model="experimental_conversations",
            enhanced=True
        )
        
        # If no more input
        response.say(
            "Is there anything else I can help you with?",
            voice="Polly.Aditi"
        )
        response.redirect(f"{settings.public_url}/voice/process-speech")
        
    except Exception as e:
        logger.error(f"Error processing speech: {str(e)}", exc_info=True)
        response.say(
            "I'm sorry, I encountered an error. Please try again.",
            voice="Polly.Joanna"
        )
        response.hangup()
    
    return Response(content=str(response), media_type="application/xml")


@app.post("/call-status")
async def call_status(request: Request):
    """Webhook for call status updates"""
    form_data = await request.form()
    call_sid = form_data.get("CallSid")
    call_status = form_data.get("CallStatus")
    answered_by = form_data.get("AnsweredBy")  # human or machine
    
    logger.info(f"Call {call_sid} status: {call_status}, answered_by: {answered_by}")
    
    # Handle answering machine detection
    if answered_by == "machine_start":
        logger.info(f"Call {call_sid} answered by machine")
        # You can leave a voicemail or handle differently
    
    # Clean up session when call ends
    if call_status in ["completed", "failed", "busy", "no-answer", "canceled"]:
        session = await session_manager.get_session(call_sid)
        if session:
            # Log conversation history before cleanup
            logger.info(f"Call {call_sid} conversation: {len(session.get('conversation_history', []))} messages")
            await session_manager.delete_session(call_sid)
            logger.info(f"Cleaned up session for call {call_sid}")
    
    return {"status": "ok"}


# @app.websocket("/media")
# async def websocket_endpoint(websocket: WebSocket):
#     """WebSocket endpoint for receiving Twilio media streams"""
#     await websocket.accept()
#     logger.info("WebSocket connection accepted")
    
#     call_sid = None
#     audio_buffer = None
    
#     try:
#         while True:
#             message = await websocket.receive_text()
#             data = json.loads(message)
            
#             event_type = data.get("event")
            
#             if event_type == "connected":
#                 logger.info(f"Connected event: {data}")
                
#             elif event_type == "start":
#                 logger.info(f"Start event: {data}")
#                 call_sid = data.get("start", {}).get("callSid")
                
#                 if call_sid:
#                     # Initialize audio buffer for this call
#                     audio_buffer = AudioBuffer(
#                         call_sid=call_sid,
#                         silence_threshold=settings.silence_threshold_seconds
#                     )
#                     active_sessions[call_sid] = {
#                         "websocket": websocket,
#                         "buffer": audio_buffer,
#                         "stream_sid": data.get("start", {}).get("streamSid"),
#                         "started_at": datetime.now().isoformat()
#                     }
#                     logger.info(f"Session created for call {call_sid}")
                    
#             elif event_type == "media":
#                 if audio_buffer is None:
#                     continue
                    
#                 # Get the base64 encoded audio payload
#                 payload = data.get("media", {}).get("payload")
#                 timestamp = data.get("media", {}).get("timestamp", 0)
                
#                 if payload:
#                     # Decode the audio chunk
#                     audio_chunk = base64.b64decode(payload)
                    
#                     # Add to buffer
#                     audio_buffer.add_chunk(audio_chunk, float(timestamp) / 1000.0)
                    
#                     # Check if silence threshold is reached
#                     current_time = float(timestamp) / 1000.0
#                     if audio_buffer.check_silence_duration(current_time):
#                         logger.info(f"Silence detected for {settings.silence_threshold_seconds}s")
                        
#                         # Get buffered audio
#                         buffered_audio = audio_buffer.get_buffered_audio()
                        
#                         # Process the audio (transcribe + generate response)
#                         await process_audio_and_respond(
#                             call_sid=call_sid,
#                             audio_data=buffered_audio,
#                             websocket=websocket
#                         )
                        
#                         # Clear buffer
#                         audio_buffer.clear_buffer()
                        
#             elif event_type == "stop":
#                 logger.info(f"Stop event: {data}")
#                 break
                
#     except WebSocketDisconnect:
#         logger.info("WebSocket disconnected")
#     except Exception as e:
#         logger.error(f"WebSocket error: {str(e)}", exc_info=True)
#     finally:
#         if call_sid and call_sid in active_sessions:
#             del active_sessions[call_sid]
#             logger.info(f"Session cleaned up for call {call_sid}")


# async def process_audio_and_respond(call_sid: str, audio_data: bytes, websocket: WebSocket):
#     """
#     Process the buffered audio, generate a response, and play it back
    
#     Args:
#         call_sid: The Twilio call SID
#         audio_data: Raw audio bytes (mulaw @ 8kHz)
#         websocket: WebSocket connection to send updates
#     """
#     logger.info(f"Processing {len(audio_data)} bytes of audio for call {call_sid}")
    
#     try:
#         # TODO: Integrate with speech-to-text service
#         # For now, we'll use a placeholder
#         transcription = await transcribe_audio(audio_data)
#         logger.info(f"Transcription: {transcription}")
        
#         # TODO: Generate AI response based on transcription
#         response_text = await generate_ai_response(transcription)
#         logger.info(f"AI Response: {response_text}")
        
#         # TODO: Convert response text to speech using MeloTTS
#         response_audio_url = await generate_tts(response_text)
#         logger.info(f"TTS audio URL: {response_audio_url}")
        
#         # Update the call to play the response
#         await play_audio_on_call(call_sid, response_audio_url)
        
#     except Exception as e:
#         logger.error(f"Error processing audio: {str(e)}", exc_info=True)


# async def transcribe_audio(audio_data: bytes) -> str:
#     """
#     Transcribe audio to text
    
#     TODO: Integrate with a speech-to-text service:
#     - Google Cloud Speech-to-Text
#     - Amazon Transcribe
#     - Azure Speech Services
#     - OpenAI Whisper
#     """
#     # Placeholder implementation
#     await asyncio.sleep(0.1)
#     return "[Transcription placeholder - integrate STT service here]"


# async def generate_ai_response(transcription: str) -> str:
#     """
#     Generate AI response based on transcription
    
#     TODO: Integrate with LLM service:
#     - OpenAI GPT
#     - Anthropic Claude
#     - Local LLM
#     """
#     # Placeholder implementation
#     await asyncio.sleep(0.1)
#     return "Thank you for your message. I'm processing your request."


async def generate_ai_response_sync(user_input: str, call_sid: str) -> str:
    """
    Generate AI response using RAG pipeline

    Args:
        user_input: The user's speech input
        call_sid: Call SID to retrieve conversation history

    Returns:
        AI-generated response text
    """
    # Get session with conversation history
    session = await session_manager.get_session(call_sid)
    if not session:
        logger.warning(f"Session not found for {call_sid}")
        return "I apologize, I'm having trouble accessing your session. Please try again."

    conversation_history = session.get('conversation_history', [])
    language = session.get('language', 'en')

    # Check for goodbye/exit intents
    goodbye_phrases = ["goodbye", "bye", "thank you", "thanks", "that's all", "nothing else", "धन्यवाद", "अलविदा"]
    if any(phrase in user_input.lower() for phrase in goodbye_phrases):
        if language == "hi-IN":
            return "कॉल करने के लिए धन्यवाद। आपका दिन शुभ हो!"
        else:
            return "Thank you for calling. Have a great day!"

    # Process with RAG pipeline if available
    if rag_pipeline and settings.enable_rag:
        try:
            response = await rag_pipeline.process_query(
                user_query=user_input,
                conversation_history=conversation_history,
                language=language,
                n_results=settings.rag_top_k
            )
            return response
        except Exception as e:
            logger.error(f"RAG pipeline error: {e}", exc_info=True)
            # Fall through to fallback responses

    # Fallback responses if RAG is disabled or fails
    user_lower = user_input.lower()

    if language == "hi-IN":
        if "help" in user_lower or "मदद" in user_lower:
            return "मैं आपकी जानकारी, सवालों के जवाब या आपकी ज़रूरतों में मदद कर सकता हूँ। आप क्या जानना चाहेंगे?"
        elif "time" in user_lower or "समय" in user_lower:
            now = datetime.now()
            return f"वर्तमान समय {now.strftime('%I:%M %p')} है।"
        elif any(word in user_lower for word in ["hello", "hi", "नमस्ते"]):
            return "नमस्ते! मैं आज आपकी कैसे मदद कर सकता हूँ?"
        else:
            return f"मैंने सुना: {user_input}। क्या आप कृपया अधिक विवरण दे सकते हैं?"
    else:
        if "help" in user_lower:
            return "I can help you with information, answer questions, or assist with your needs. What would you like to know?"
        elif "time" in user_lower:
            now = datetime.now()
            return f"The current time is {now.strftime('%I:%M %p')}."
        elif any(word in user_lower for word in ["hello", "hi", "hey"]):
            return "Hello! How can I help you today?"
        else:
            return f"I heard: {user_input}. Could you please provide more details or ask a specific question?"


async def generate_tts(text: str) -> str:
    """
    Generate speech from text using MeloTTS or other TTS service
    
    TODO: Integrate with MeloTTS:
    - Use the MeloTTS library in this project
    - Generate audio file
    - Upload to accessible URL (S3, etc.)
    - Return public URL
    """
    # Placeholder - return a Twilio demo URL
    await asyncio.sleep(0.1)
    return "http://demo.twilio.com/docs/voice.xml"


async def play_audio_on_call(call_sid: str, audio_url: str):
    """
    Update an active call to play audio
    
    Args:
        call_sid: The call SID to update
        audio_url: URL of the audio file to play
    """
    try:
        # Create TwiML to play the audio
        response = VoiceResponse()
        response.play(audio_url)
        response.pause(length=1)
        
        # Update the call with new TwiML
        call = twilio_client.calls(call_sid).update(
            twiml=str(response)
        )
        
        logger.info(f"Updated call {call_sid} to play audio: {audio_url}")
        
    except Exception as e:
        logger.error(f"Error updating call: {str(e)}", exc_info=True)


@app.post("/interrupt-call/{call_sid}")
async def interrupt_call(call_sid: str):
    """
    Interrupt/pause any audio currently playing on a call

    This endpoint can be called when the user starts speaking again
    """
    try:
        if not await session_manager.session_exists(call_sid):
            raise HTTPException(status_code=404, detail="Call session not found")
        
        # Update call to stop current TwiML and listen
        response = VoiceResponse()
        response.pause(length=1)
        
        call = twilio_client.calls(call_sid).update(
            twiml=str(response)
        )
        
        logger.info(f"Interrupted call {call_sid}")
        
        return {"success": True, "call_sid": call_sid}
        
    except Exception as e:
        logger.error(f"Error interrupting call: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """
    Health check endpoint

    Returns the health status of all system components
    """
    health = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {}
    }

    # Check Redis
    try:
        await redis_client.ping()
        health["components"]["redis"] = {"status": "healthy", "message": "Connected"}
    except Exception as e:
        health["components"]["redis"] = {"status": "unhealthy", "message": str(e)}
        health["status"] = "degraded"

    # Check Chroma
    try:
        if chroma_client:
            collection = chroma_client.get_collection(settings.chroma_collection_name)
            count = collection.count()
            health["components"]["chroma"] = {
                "status": "healthy",
                "message": f"Collection has {count} documents"
            }
        else:
            health["components"]["chroma"] = {
                "status": "not_initialized",
                "message": "Chroma client not initialized"
            }
    except Exception as e:
        health["components"]["chroma"] = {"status": "unhealthy", "message": str(e)}
        health["status"] = "degraded"

    # Check RAG Pipeline
    if rag_pipeline:
        health["components"]["rag_pipeline"] = {
            "status": "healthy",
            "message": "RAG pipeline initialized"
        }
    else:
        health["components"]["rag_pipeline"] = {
            "status": "disabled",
            "message": "RAG pipeline not initialized (check Gemini API key)"
        }
        if health["status"] == "healthy":
            health["status"] = "degraded"

    # Check Twilio
    try:
        # Quick validation that client is configured
        if twilio_client.account_sid:
            health["components"]["twilio"] = {
                "status": "healthy",
                "message": "Twilio client configured"
            }
    except Exception as e:
        health["components"]["twilio"] = {"status": "unhealthy", "message": str(e)}
        health["status"] = "degraded"

    return health


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=True,
        log_level="info"
    )
