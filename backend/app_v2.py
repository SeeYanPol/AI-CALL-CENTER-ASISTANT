"""
CallSim AI Call Center API - v2.0
Refactored with production-ready features
"""

import os
import io
import uuid
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, request, jsonify, send_file, g
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import JWTManager
from flask_talisman import Talisman
from flask_bcrypt import Bcrypt
from marshmallow import ValidationError
from flasgger import Swagger
from dotenv import load_dotenv
import openai
from gtts import gTTS
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

# Import local modules
from config import config
from database import init_db, get_db_session
from redis_config import init_redis, redis_config
from models import User, CallSession, ChatMessage, UserRole
from schemas import (
    UserRegistrationSchema, UserLoginSchema, SessionStartSchema,
    ChatMessageSchema, TTSRequestSchema, SessionQuerySchema
)
from auth import (
    authenticate_user, create_user, generate_tokens,
    jwt_required_custom, role_required, require_api_key_or_jwt,
    log_audit_event, get_current_user
)

# Load environment variables
load_dotenv()

# Initialize Sentry for error tracking
sentry_dsn = os.getenv('SENTRY_DSN')
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[FlaskIntegration()],
        traces_sample_rate=0.1,
        environment=os.getenv('FLASK_ENV', 'development')
    )

# Create Flask app
app = Flask(__name__)

# Load configuration
env = os.getenv('FLASK_ENV', 'development')
app.config.from_object(config[env])
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', os.getenv('FLASK_SECRET_KEY'))
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)

# Initialize extensions
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# Security headers (Talisman)
if env == 'production':
    Talisman(app, force_https=True)

# CORS configuration
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:5500').split(',')
CORS(app, origins=ALLOWED_ORIGINS, supports_credentials=True)

# Rate limiting with Redis
limiter = Limiter(
    app=app,
    key_func=lambda: getattr(g, 'current_user', None).id if hasattr(g, 'current_user') and g.current_user else get_remote_address(),
    storage_uri=os.getenv('RATELIMIT_STORAGE_URL', 'memory://'),
    default_limits=[]  # Set per-route
)

# Swagger API documentation
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/apispec.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/api/docs"
}

swagger = Swagger(app, config=swagger_config, template={
    "info": {
        "title": "CallSim AI Call Center API",
        "description": "Production-ready API for AI-powered call center training",
        "version": "2.0.0",
        "contact": {
            "name": "CallSim Support",
            "email": "support@callsim.com"
        }
    },
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "JWT Authorization header using the Bearer scheme. Example: 'Bearer {token}'"
        },
        "ApiKey": {
            "type": "apiKey",
            "name": "X-API-Key",
            "in": "header"
        }
    }
})

# Initialize database and Redis
init_db(app)
init_redis(app)

# Configure OpenAI
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

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


# ============================================
# HEALTH & STATUS ENDPOINTS
# ============================================

@app.route('/api/health', methods=['GET'])
@limiter.exempt
def health_check():
    """
    Health check endpoint
    ---
    tags:
      - System
    responses:
      200:
        description: System health status
    """
    db_healthy = app.db.health_check()
    redis_healthy = app.redis.health_check()
    
    status = 'healthy' if (db_healthy and redis_healthy) else 'degraded'
    
    return jsonify({
        'status': status,
        'timestamp': datetime.utcnow().isoformat(),
        'version': '2.0.0',
        'services': {
            'database': 'healthy' if db_healthy else 'unhealthy',
            'redis': 'healthy' if redis_healthy else 'unhealthy',
            'openai': 'configured' if OPENAI_API_KEY else 'not_configured'
        }
    }), 200 if status == 'healthy' else 503


# ============================================
# AUTHENTICATION ENDPOINTS
# ============================================

@app.route('/api/v1/auth/register', methods=['POST'])
@limiter.limit("5 per hour")
def register():
    """
    Register a new user
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - email
            - password
            - full_name
          properties:
            email:
              type: string
              format: email
            password:
              type: string
              minLength: 8
            full_name:
              type: string
            role:
              type: string
              enum: [admin, trainer, trainee]
              default: trainee
    responses:
      201:
        description: User created successfully
      400:
        description: Validation error
      409:
        description: User already exists
    """
    try:
        schema = UserRegistrationSchema()
        data = schema.load(request.json)
        
        user = create_user(
            email=data['email'],
            password=data['password'],
            full_name=data['full_name'],
            role=data.get('role', 'trainee')
        )
        
        access_token, refresh_token = generate_tokens(user.id, user.role.value)
        
        return jsonify({
            'message': 'User created successfully',
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 201
        
    except ValidationError as e:
        return jsonify({'error': 'Validation failed', 'details': e.messages}), 400
    except ValueError as e:
        return jsonify({'error': str(e)}), 409
    except Exception as e:
        app.logger.error(f"Registration error: {str(e)}")
        return jsonify({'error': 'Registration failed'}), 500


@app.route('/api/v1/auth/login', methods=['POST'])
@limiter.limit("10 per hour")
def login():
    """
    User login
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - email
            - password
          properties:
            email:
              type: string
            password:
              type: string
    responses:
      200:
        description: Login successful
      401:
        description: Invalid credentials
    """
    try:
        schema = UserLoginSchema()
        data = schema.load(request.json)
        
        result = authenticate_user(data['email'], data['password'])
        
        return jsonify(result), 200
        
    except ValidationError as e:
        return jsonify({'error': 'Validation failed', 'details': e.messages}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 401


@app.route('/api/v1/auth/me', methods=['GET'])
@jwt_required_custom
def get_current_user_info():
    """
    Get current user information
    ---
    tags:
      - Authentication
    security:
      - Bearer: []
    responses:
      200:
        description: Current user info
      401:
        description: Unauthorized
    """
    return jsonify({'user': g.current_user.to_dict()}), 200


# ============================================
# CALL SESSION ENDPOINTS
# ============================================

@app.route('/api/v1/session/start', methods=['POST'])
@limiter.limit("30 per hour")
@jwt_required_custom
def start_session():
    """
    Start a new call session
    ---
    tags:
      - Sessions
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        schema:
          type: object
          properties:
            caller_info:
              type: object
    responses:
      201:
        description: Session started
      401:
        description: Unauthorized
    """
    try:
        schema = SessionStartSchema()
        data = schema.load(request.json or {})
        
        db_session = get_db_session()
        
        # Create call session
        session_token = uuid.uuid4().hex
        call_session = CallSession(
            user_id=g.current_user.id,
            session_token=session_token,
            caller_info=data.get('caller_info', {}),
            status='active'
        )
        
        db_session.add(call_session)
        db_session.commit()
        
        # Initial greeting
        greeting = "Hello! Thank you for calling. My name is Alex, how may I assist you today?"
        
        # Save greeting message
        message = ChatMessage(
            session_id=call_session.id,
            role='assistant',
            content=greeting,
            speaker='Agent'
        )
        db_session.add(message)
        db_session.commit()
        
        # Store session data in Redis
        redis_config.save_session(call_session.id, {
            'user_id': g.current_user.id,
            'token': session_token,
            'created_at': datetime.utcnow().isoformat(),
            'messages': [{'role': 'assistant', 'content': greeting}]
        })
        
        db_session.close()
        
        log_audit_event('session_start', 'session', 'create')
        
        return jsonify({
            'session_id': call_session.id,
            'token': session_token,
            'greeting': greeting
        }), 201
        
    except ValidationError as e:
        return jsonify({'error': 'Validation failed', 'details': e.messages}), 400
    except Exception as e:
        app.logger.error(f"Session start error: {str(e)}")
        return jsonify({'error': 'Failed to start session'}), 500


@app.route('/api/v1/session/<session_id>/end', methods=['POST'])
@jwt_required_custom
def end_session(session_id):
    """
    End a call session
    ---
    tags:
      - Sessions
    security:
      - Bearer: []
    parameters:
      - in: path
        name: session_id
        type: string
        required: true
    responses:
      200:
        description: Session ended
      404:
        description: Session not found
    """
    db_session = get_db_session()
    
    try:
        call_session = db_session.query(CallSession).filter_by(
            id=session_id,
            user_id=g.current_user.id
        ).first()
        
        if not call_session:
            return jsonify({'error': 'Session not found'}), 404
        
        # Update session
        call_session.status = 'ended'
        call_session.ended_at = datetime.utcnow()
        call_session.duration_seconds = int((call_session.ended_at - call_session.started_at).total_seconds())
        
        # Get transcript
        messages = db_session.query(ChatMessage).filter_by(session_id=session_id).all()
        transcript = [msg.to_dict() for msg in messages]
        
        call_session.message_count = len(messages)
        
        db_session.commit()
        
        # Remove from Redis
        redis_config.delete_session(session_id)
        
        log_audit_event('session_end', 'session', 'end')
        
        return jsonify({
            'status': 'ended',
            'session': call_session.to_dict(),
            'transcript': transcript
        }), 200
        
    except Exception as e:
        app.logger.error(f"Session end error: {str(e)}")
        return jsonify({'error': 'Failed to end session'}), 500
    finally:
        db_session.close()


@app.route('/api/v1/sessions', methods=['GET'])
@jwt_required_custom
def list_sessions():
    """
    List user's call sessions
    ---
    tags:
      - Sessions
    security:
      - Bearer: []
    parameters:
      - in: query
        name: page
        type: integer
        default: 1
      - in: query
        name: per_page
        type: integer
        default: 20
      - in: query
        name: status
        type: string
        enum: [active, ended, abandoned]
    responses:
      200:
        description: List of sessions
    """
    try:
        schema = SessionQuerySchema()
        params = schema.load(request.args)
        
        db_session = get_db_session()
        
        query = db_session.query(CallSession).filter_by(user_id=g.current_user.id)
        
        if params.get('status'):
            query = query.filter_by(status=params['status'])
        
        # Pagination
        page = params.get('page', 1)
        per_page = params.get('per_page', 20)
        
        sessions = query.order_by(CallSession.started_at.desc()).offset(
            (page - 1) * per_page
        ).limit(per_page).all()
        
        total = query.count()
        
        db_session.close()
        
        return jsonify({
            'sessions': [s.to_dict() for s in sessions],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        }), 200
        
    except ValidationError as e:
        return jsonify({'error': 'Validation failed', 'details': e.messages}), 400
    except Exception as e:
        app.logger.error(f"List sessions error: {str(e)}")
        return jsonify({'error': 'Failed to list sessions'}), 500


# ============================================
# CHAT & AI ENDPOINTS
# ============================================

@app.route('/api/v1/chat', methods=['POST'])
@limiter.limit("60 per hour")
@jwt_required_custom
def chat():
    """
    Send a chat message and get AI response
    ---
    tags:
      - Chat
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - message
          properties:
            message:
              type: string
            session_id:
              type: string
    responses:
      200:
        description: AI response
      400:
        description: Validation error
    """
    try:
        schema = ChatMessageSchema()
        data = schema.load(request.json)
        
        user_message = data['message']
        session_id = data.get('session_id')
        
        db_session = get_db_session()
        messages_history = []
        
        # Validate session if provided
        if session_id:
            call_session = db_session.query(CallSession).filter_by(
                id=session_id,
                user_id=g.current_user.id
            ).first()
            
            if not call_session:
                db_session.close()
                return jsonify({'error': 'Session not found'}), 404
            
            # Save user message
            user_msg = ChatMessage(
                session_id=session_id,
                role='user',
                content=user_message,
                speaker='Caller'
            )
            db_session.add(user_msg)
            
            # Get message history
            messages = db_session.query(ChatMessage).filter_by(
                session_id=session_id
            ).order_by(ChatMessage.timestamp).all()
            
            messages_history = [{'role': msg.role, 'content': msg.content} for msg in messages]
        
        # Generate AI response
        try:
            if OPENAI_API_KEY:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": CALL_CENTER_SYSTEM_PROMPT},
                        *messages_history,
                        {"role": "user", "content": user_message}
                    ],
                    max_tokens=150,
                    temperature=0.7
                )
                ai_response = response.choices[0].message.content.strip()
                tokens_used = response.usage.total_tokens
            else:
                ai_response = generate_fallback_response(user_message)
                tokens_used = None
                
        except Exception as e:
            app.logger.error(f"AI response error: {str(e)}")
            ai_response = "I apologize, I'm having trouble processing that. Could you please repeat?"
            tokens_used = None
        
        # Save AI response if in session
        if session_id:
            ai_msg = ChatMessage(
                session_id=session_id,
                role='assistant',
                content=ai_response,
                speaker='Agent',
                tokens_used=tokens_used
            )
            db_session.add(ai_msg)
            db_session.commit()
        
        db_session.close()
        
        return jsonify({
            'response': ai_response,
            'session_id': session_id
        }), 200
        
    except ValidationError as e:
        return jsonify({'error': 'Validation failed', 'details': e.messages}), 400
    except Exception as e:
        app.logger.error(f"Chat error: {str(e)}")
        return jsonify({'error': 'Chat failed'}), 500


# ============================================
# TEXT-TO-SPEECH ENDPOINTS
# ============================================

@app.route('/api/v1/tts', methods=['POST'])
@limiter.limit("30 per hour")
@require_api_key_or_jwt
def text_to_speech():
    """
    Convert text to speech
    ---
    tags:
      - TTS
    security:
      - Bearer: []
      - ApiKey: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - text
          properties:
            text:
              type: string
            lang:
              type: string
              default: en
    responses:
      200:
        description: Audio file
        content:
          audio/mpeg:
            schema:
              type: string
              format: binary
    """
    try:
        schema = TTSRequestSchema()
        data = schema.load(request.json)
        
        text = data['text']
        lang = data.get('lang', 'en')
        
        # Check cache first
        cache_key = f"tts:{lang}:{hash(text)}"
        cached_audio = redis_config.cache_get(cache_key)
        
        if cached_audio:
            # Return cached audio
            audio_buffer = io.BytesIO(bytes.fromhex(cached_audio))
            audio_buffer.seek(0)
        else:
            # Generate TTS
            tts = gTTS(text=text, lang=lang, slow=False)
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            
            # Cache for 1 hour
            redis_config.cache_set(cache_key, audio_buffer.getvalue().hex(), ttl=3600)
            audio_buffer.seek(0)
        
        return send_file(
            audio_buffer,
            mimetype='audio/mpeg',
            as_attachment=False,
            download_name='speech.mp3'
        )
        
    except ValidationError as e:
        return jsonify({'error': 'Validation failed', 'details': e.messages}), 400
    except Exception as e:
        app.logger.error(f"TTS error: {str(e)}")
        return jsonify({'error': 'TTS failed'}), 500


# ============================================
# ADMIN ENDPOINTS
# ============================================

@app.route('/api/v1/admin/users', methods=['GET'])
@role_required('admin')
def list_all_users():
    """
    List all users (admin only)
    ---
    tags:
      - Admin
    security:
      - Bearer: []
    responses:
      200:
        description: List of users
      403:
        description: Forbidden
    """
    db_session = get_db_session()
    
    try:
        users = db_session.query(User).all()
        return jsonify({
            'users': [u.to_dict() for u in users]
        }), 200
    finally:
        db_session.close()


# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(429)
def ratelimit_handler(e):
    log_audit_event('rate_limit_exceeded', 'api', 'request', status_code=429)
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


@app.errorhandler(404)
def not_found(e):
    return jsonify({
        'error': 'Not found',
        'message': 'The requested resource was not found.'
    }), 404


# ============================================
# HELPER FUNCTIONS
# ============================================

def generate_fallback_response(user_message):
    """Generate fallback responses when OpenAI is not available"""
    user_lower = user_message.lower()
    
    if any(word in user_lower for word in ['hello', 'hi', 'hey']):
        return "Hello! How can I help you today?"
    elif any(word in user_lower for word in ['problem', 'issue', 'broken', 'not working']):
        return "I'm sorry to hear you're experiencing issues. Can you please describe what's happening in more detail?"
    elif any(word in user_lower for word in ['refund', 'money back', 'return']):
        return "I understand you'd like to discuss a refund. Let me look into that for you. Can you provide your order number?"
    elif any(word in user_lower for word in ['thank', 'thanks']):
        return "You're welcome! Is there anything else I can help you with today?"
    elif any(word in user_lower for word in ['bye', 'goodbye']):
        return "Thank you for calling. Have a wonderful day! Goodbye."
    else:
        return "I understand. Could you please provide more details so I can better assist you?"


# ============================================
# APPLICATION STARTUP
# ============================================

if __name__ == '__main__':
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.getenv('PORT', 5000))
    
    # Create tables if they don't exist
    app.db.create_all()
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug_mode
    )
