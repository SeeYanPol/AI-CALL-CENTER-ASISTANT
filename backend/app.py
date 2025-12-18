"""
CallSim AI Call Center API
Secure Flask backend with TTS and AI chat capabilities
"""

import os
import io
import uuid
import hashlib
import secrets
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, request, jsonify, send_file, session
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
import openai
from gtts import gTTS

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Security configurations
app.secret_key = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(32))
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# CORS configuration - restrict to your frontend origin
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:5500,http://127.0.0.1:5500').split(',')
CORS(app, origins=ALLOWED_ORIGINS, supports_credentials=True)

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["100 per hour", "10 per minute"]
)

# API Key for authentication
API_KEY = os.getenv('API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Configure OpenAI
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

# Store for active sessions and tokens
active_sessions = {}

# System prompt for call center AI
CALL_CENTER_SYSTEM_PROMPT = """You are a professional, empathetic AI call center agent for a customer service hotline. 

Your responsibilities:
- Greet customers warmly and professionally
- Listen to their concerns and acknowledge their feelings
- Ask clarifying questions when needed
- Provide helpful solutions and information
- Remain calm and patient at all times
- Use clear, simple language
- End calls politely and ensure customer satisfaction

Guidelines:
- Keep responses concise (2-3 sentences max for natural conversation)
- Use appropriate filler words occasionally for natural speech
- Show empathy: "I understand", "I apologize for the inconvenience"
- Be solution-oriented
- Never be rude or dismissive

You are currently on a live call. Respond naturally as if speaking."""


def require_api_key(f):
    """Decorator to require API key authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('X-API-Key')
        
        if not API_KEY:
            # If no API key is configured, allow access (dev mode)
            return f(*args, **kwargs)
            
        if not auth_header or not secrets.compare_digest(auth_header, API_KEY):
            return jsonify({'error': 'Unauthorized', 'message': 'Invalid or missing API key'}), 401
            
        return f(*args, **kwargs)
    return decorated


def generate_session_token():
    """Generate a secure session token"""
    return secrets.token_urlsafe(32)


def validate_input(text, max_length=1000):
    """Sanitize and validate user input"""
    if not text or not isinstance(text, str):
        return None
    # Strip and limit length
    text = text.strip()[:max_length]
    # Basic sanitization
    return text


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })


@app.route('/api/session/start', methods=['POST'])
@limiter.limit("5 per minute")
@require_api_key
def start_session():
    """Start a new call session"""
    session_token = generate_session_token()
    session_id = str(uuid.uuid4())
    
    active_sessions[session_id] = {
        'token': session_token,
        'created_at': datetime.utcnow(),
        'messages': [],
        'caller_info': request.json.get('caller_info', {}),
        'transcript': []
    }
    
    # Initial greeting
    greeting = "Hello! Thank you for calling. My name is Alex, how may I assist you today?"
    active_sessions[session_id]['messages'].append({
        'role': 'assistant',
        'content': greeting
    })
    active_sessions[session_id]['transcript'].append({
        'speaker': 'Agent',
        'text': greeting,
        'timestamp': datetime.utcnow().isoformat()
    })
    
    return jsonify({
        'session_id': session_id,
        'token': session_token,
        'greeting': greeting
    })


@app.route('/api/session/<session_id>/end', methods=['POST'])
@require_api_key
def end_session(session_id):
    """End a call session and get summary"""
    token = request.headers.get('X-Session-Token')
    
    if session_id not in active_sessions:
        return jsonify({'error': 'Session not found'}), 404
        
    session_data = active_sessions[session_id]
    
    if not secrets.compare_digest(session_data['token'], token or ''):
        return jsonify({'error': 'Invalid session token'}), 401
    
    # Get transcript
    transcript = session_data.get('transcript', [])
    
    # Clean up session
    del active_sessions[session_id]
    
    return jsonify({
        'status': 'ended',
        'transcript': transcript,
        'message': 'Call session ended successfully'
    })


@app.route('/api/chat', methods=['POST'])
@limiter.limit("30 per minute")
@require_api_key
def chat():
    """Process user message and get AI response"""
    data = request.json
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    user_message = validate_input(data.get('message'))
    session_id = data.get('session_id')
    token = request.headers.get('X-Session-Token')
    
    if not user_message:
        return jsonify({'error': 'Message is required'}), 400
    
    # Validate session if provided
    if session_id:
        if session_id not in active_sessions:
            return jsonify({'error': 'Session not found'}), 404
        
        session_data = active_sessions[session_id]
        
        if not secrets.compare_digest(session_data['token'], token or ''):
            return jsonify({'error': 'Invalid session token'}), 401
        
        # Add user message to history
        session_data['messages'].append({
            'role': 'user',
            'content': user_message
        })
        session_data['transcript'].append({
            'speaker': 'Caller',
            'text': user_message,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        messages = session_data['messages']
    else:
        messages = [{'role': 'user', 'content': user_message}]
    
    # Generate AI response
    try:
        if OPENAI_API_KEY:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": CALL_CENTER_SYSTEM_PROMPT},
                    *messages
                ],
                max_tokens=150,
                temperature=0.7
            )
            ai_response = response.choices[0].message.content.strip()
        else:
            # Fallback responses if no OpenAI key
            ai_response = generate_fallback_response(user_message)
            
    except Exception as e:
        app.logger.error(f"AI response error: {str(e)}")
        ai_response = "I apologize, I'm having trouble processing that. Could you please repeat what you said?"
    
    # Store response in session
    if session_id and session_id in active_sessions:
        active_sessions[session_id]['messages'].append({
            'role': 'assistant',
            'content': ai_response
        })
        active_sessions[session_id]['transcript'].append({
            'speaker': 'Agent',
            'text': ai_response,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    return jsonify({
        'response': ai_response,
        'session_id': session_id
    })


@app.route('/api/tts', methods=['POST'])
@limiter.limit("20 per minute")
@require_api_key
def text_to_speech():
    """Convert text to speech audio"""
    data = request.json
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    text = validate_input(data.get('text'), max_length=500)
    lang = data.get('lang', 'en')
    
    if not text:
        return jsonify({'error': 'Text is required'}), 400
    
    # Validate language
    allowed_langs = ['en', 'es', 'fr', 'de', 'it', 'pt', 'ja', 'ko', 'zh-CN']
    if lang not in allowed_langs:
        lang = 'en'
    
    try:
        # Generate TTS using gTTS
        tts = gTTS(text=text, lang=lang, slow=False)
        
        # Save to memory buffer
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        
        return send_file(
            audio_buffer,
            mimetype='audio/mpeg',
            as_attachment=False,
            download_name='speech.mp3'
        )
        
    except Exception as e:
        app.logger.error(f"TTS error: {str(e)}")
        return jsonify({'error': 'Failed to generate speech'}), 500


@app.route('/api/tts/voices', methods=['GET'])
@require_api_key
def get_voices():
    """Get available TTS voices"""
    voices = [
        {'id': 'en', 'name': 'English (US)', 'lang': 'en'},
        {'id': 'en-uk', 'name': 'English (UK)', 'lang': 'en-uk'},
        {'id': 'es', 'name': 'Spanish', 'lang': 'es'},
        {'id': 'fr', 'name': 'French', 'lang': 'fr'},
        {'id': 'de', 'name': 'German', 'lang': 'de'},
    ]
    return jsonify({'voices': voices})


def generate_fallback_response(user_message):
    """Generate fallback responses when OpenAI is not available"""
    user_lower = user_message.lower()
    
    # Simple keyword-based responses
    if any(word in user_lower for word in ['hello', 'hi', 'hey']):
        return "Hello! How can I help you today?"
    
    elif any(word in user_lower for word in ['problem', 'issue', 'broken', 'not working']):
        return "I'm sorry to hear you're experiencing issues. Can you please describe what's happening in more detail?"
    
    elif any(word in user_lower for word in ['refund', 'money back', 'return']):
        return "I understand you'd like to discuss a refund. Let me look into that for you. Can you provide your order number?"
    
    elif any(word in user_lower for word in ['billing', 'charge', 'payment']):
        return "I can help you with billing questions. Could you tell me more about the specific charge you're asking about?"
    
    elif any(word in user_lower for word in ['thank', 'thanks']):
        return "You're welcome! Is there anything else I can help you with today?"
    
    elif any(word in user_lower for word in ['bye', 'goodbye', 'that\'s all']):
        return "Thank you for calling. Have a wonderful day! Goodbye."
    
    elif any(word in user_lower for word in ['speak', 'manager', 'supervisor']):
        return "I understand you'd like to speak with a supervisor. Please hold while I transfer your call."
    
    else:
        return "I understand. Could you please provide more details so I can better assist you?"


# Error handlers
@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({
        'error': 'Rate limit exceeded',
        'message': 'Too many requests. Please try again later.'
    }), 429


@app.errorhandler(500)
def internal_error(e):
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred.'
    }), 500


if __name__ == '__main__':
    # Development server - use gunicorn/waitress for production
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.getenv('PORT', 5000))
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug_mode
    )
