"""
CallSim AI Call Center - Simple Development Version
For Senior High School Project
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
from flask_bcrypt import Bcrypt
from marshmallow import ValidationError
from flasgger import Swagger
from dotenv import load_dotenv
from google.cloud import aiplatform
from vertexai.preview.generative_models import GenerativeModel
import vertexai
from gtts import gTTS

# Import local modules
from database import init_db, get_db_session
from models import User, CallSession, ChatMessage
from schemas import (
    UserRegistrationSchema, UserLoginSchema, SessionStartSchema,
    ChatMessageSchema, TTSRequestSchema
)
from auth import (
    authenticate_user, create_user, generate_tokens,
    jwt_required_custom, role_required, log_audit_event
)

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'dev-jwt-key')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)

# Initialize extensions
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# CORS configuration
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:5500').split(',')
CORS(app, 
     origins=ALLOWED_ORIGINS, 
     supports_credentials=True,
     allow_headers=['Content-Type', 'Authorization', 'X-API-Key', 'X-Session-Token'],
     expose_headers=['Content-Type', 'X-Session-Token'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
)

# Simple rate limiting (in-memory for development)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per hour"]
)

# Swagger API documentation
swagger = Swagger(app, template={
    "info": {
        "title": "CallSim AI Call Center API",
        "description": "Senior High School Project - AI Call Center Training System",
        "version": "1.0.0"
    }
})

# Initialize database
init_db(app)

# Configure Vertex AI
GOOGLE_CLOUD_PROJECT = os.getenv('GOOGLE_CLOUD_PROJECT')
GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

if GOOGLE_CLOUD_PROJECT:
    vertexai.init(project=GOOGLE_CLOUD_PROJECT, location="us-central1")
    gemini_model = GenerativeModel("gemini-1.5-flash")
else:
    gemini_model = None

# System prompt for Lazada call center AI
LAZADA_SYSTEM_PROMPT = """You are a professional Lazada Customer Support Agent handling customer calls.

**CRITICAL CONSTRAINTS - You may ONLY assist with these topics:**
1. **Delivery Issues**: Late packages, tracking numbers, rider location, delivery status
2. **Order Problems**: Wrong items received, missing items, damaged goods, order cancellation, refunds
3. **Internet/App Issues**: App not loading, connection errors, login problems, website issues

**BEHAVIOR RULES:**
- Keep responses SHORT (maximum 2 sentences) for faster audio generation
- Be empathetic but professional: "I understand your concern", "I apologize for the inconvenience"
- If the topic is NOT related to Delivery, Orders, or Internet issues, respond with:
  "I apologize, but I can only assist with delivery, order, or app-related issues. For other concerns, please contact our main hotline at 123-4567."
- Ask clarifying questions when needed (order number, tracking ID, etc.)
- Provide specific solutions when possible
- Always end with "Is there anything else I can help you with?"

**RESPONSE FORMAT:**
- Acknowledge the issue
- Provide solution or next steps
- Keep it conversational and natural

You are on a live call. Respond as a real support agent would speak."""


# In-memory session storage (simple cache)
session_cache = {}


# ============================================
# HEALTH & STATUS ENDPOINTS
# ============================================

@app.route('/api/health', methods=['GET'])
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
    
    return jsonify({
        'status': 'healthy' if db_healthy else 'degraded',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0',
        'database': 'healthy' if db_healthy else 'unhealthy',
        'vertex_ai': 'configured' if GOOGLE_CLOUD_PROJECT else 'not_configured'
    }), 200


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
            password:
              type: string
            full_name:
              type: string
            role:
              type: string
              enum: [admin, trainer, trainee]
    responses:
      201:
        description: User created successfully
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
    """Get current user information"""
    return jsonify({'user': g.current_user.to_dict()}), 200


# ============================================
# CALL SESSION ENDPOINTS
# ============================================

@app.route('/api/v1/session/start', methods=['POST'])
@limiter.limit("30 per hour")
@jwt_required_custom
def start_session():
    """Start a new call session"""
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
        greeting = "Hello! Thank you for calling Lazada Customer Support. I can assist you with delivery issues, order problems, or app-related concerns. How may I help you today?"
        
        # Save greeting message
        message = ChatMessage(
            session_id=call_session.id,
            role='assistant',
            content=greeting,
            speaker='Agent'
        )
        db_session.add(message)
        db_session.commit()
        
        # Cache in memory
        session_cache[call_session.id] = {
            'user_id': g.current_user.id,
            'messages': [{'role': 'assistant', 'content': greeting}]
        }
        
        db_session.close()
        
        return jsonify({
            'session_id': call_session.id,
            'token': session_token,
            'greeting': greeting
        }), 201
        
    except Exception as e:
        app.logger.error(f"Session start error: {str(e)}")
        return jsonify({'error': 'Failed to start session'}), 500


@app.route('/api/v1/session/<session_id>/end', methods=['POST'])
@jwt_required_custom
def end_session(session_id):
    """End a call session"""
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
        
        # Remove from cache
        if session_id in session_cache:
            del session_cache[session_id]
        
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
    """List user's call sessions"""
    try:
        db_session = get_db_session()
        
        # Get page and per_page from query params
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        query = db_session.query(CallSession).filter_by(user_id=g.current_user.id)
        
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
    """Send a chat message and get AI response"""
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
        
        # Generate AI response using Vertex AI
        try:
            if gemini_model:
                # Build conversation history for Gemini
                conversation_parts = [LAZADA_SYSTEM_PROMPT]
                for msg in messages_history:
                    conversation_parts.append(f"{msg['role'].title()}: {msg['content']}")
                conversation_parts.append(f"User: {user_message}")
                
                prompt = "\n\n".join(conversation_parts)
                
                response = gemini_model.generate_content(
                    prompt,
                    generation_config={
                        "max_output_tokens": 150,
                        "temperature": 0.7,
                        "top_p": 0.8,
                    }
                )
                ai_response = response.text.strip()
            else:
                ai_response = generate_lazada_fallback_response(user_message)
                
        except Exception as e:
            app.logger.error(f"AI response error: {str(e)}")
            ai_response = "I apologize, I'm having technical difficulties. Could you please repeat your concern?"
        
        # Save AI response if in session
        if session_id:
            ai_msg = ChatMessage(
                session_id=session_id,
                role='assistant',
                content=ai_response,
                speaker='Agent'
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
def text_to_speech():
    """Convert text to speech"""
    try:
        schema = TTSRequestSchema()
        data = schema.load(request.json)
        
        text = data['text']
        lang = data.get('lang', 'en')
        
        # Generate TTS
        tts = gTTS(text=text, lang=lang, slow=False)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
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
    """List all users (admin only)"""
    db_session = get_db_session()
    
    try:
        users = db_session.query(User).all()
        return jsonify({
            'users': [u.to_dict() for u in users]
        }), 200
    finally:
        db_session.close()


@app.route('/api/v1/admin/evaluations', methods=['GET'])
@role_required('admin')
def get_all_evaluations():
    """Get all call sessions for evaluation (admin/trainer only)"""
    db_session = get_db_session()
    
    try:
        # Get filter params
        user_id = request.args.get('user_id')
        status = request.args.get('status', 'ended')
        limit = int(request.args.get('limit', 50))
        
        query = db_session.query(CallSession).filter_by(status=status)
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        sessions = query.order_by(CallSession.started_at.desc()).limit(limit).all()
        
        # Build detailed response with transcripts
        evaluations = []
        for session in sessions:
            messages = db_session.query(ChatMessage).filter_by(
                session_id=session.id
            ).order_by(ChatMessage.timestamp).all()
            
            evaluations.append({
                **session.to_dict(),
                'transcript': [msg.to_dict() for msg in messages],
                'user': session.user.to_dict() if session.user else None
            })
        
        return jsonify({
            'evaluations': evaluations,
            'total': len(evaluations)
        }), 200
        
    except Exception as e:
        app.logger.error(f"Get evaluations error: {str(e)}")
        return jsonify({'error': 'Failed to fetch evaluations'}), 500
    finally:
        db_session.close()


@app.route('/api/v1/session/<session_id>/evaluate', methods=['POST'])
@role_required('admin')
def evaluate_session(session_id):
    """Evaluate a call session with scores"""
    db_session = get_db_session()
    
    try:
        data = request.json
        
        call_session = db_session.query(CallSession).filter_by(id=session_id).first()
        
        if not call_session:
            return jsonify({'error': 'Session not found'}), 404
        
        # Update scores
        call_session.overall_score = data.get('overall_score')
        call_session.empathy_score = data.get('empathy_score')
        call_session.clarity_score = data.get('clarity_score')
        call_session.problem_solving_score = data.get('problem_solving_score')
        
        db_session.commit()
        
        return jsonify({
            'message': 'Session evaluated successfully',
            'session': call_session.to_dict()
        }), 200
        
    except Exception as e:
        app.logger.error(f"Evaluate session error: {str(e)}")
        return jsonify({'error': 'Failed to evaluate session'}), 500
    finally:
        db_session.close()


# ============================================
# HELPER FUNCTIONS
# ============================================

def generate_lazada_fallback_response(user_message):
    """Generate fallback responses when Vertex AI is not available"""
    user_lower = user_message.lower()
    
    # Check if query is within allowed topics
    delivery_keywords = ['delivery', 'rider', 'late', 'tracking', 'package', 'shipping', 'where is my']
    order_keywords = ['order', 'wrong item', 'refund', 'cancel', 'damaged', 'missing', 'return']
    internet_keywords = ['app', 'website', 'login', 'internet', 'connection', 'loading', 'error']
    
    is_allowed_topic = any([
        any(word in user_lower for word in delivery_keywords),
        any(word in user_lower for word in order_keywords),
        any(word in user_lower for word in internet_keywords)
    ])
    
    if not is_allowed_topic and not any(word in user_lower for word in ['hello', 'hi', 'hey', 'thank']):
        return "I apologize, but I can only assist with delivery, order, or app-related issues. For other concerns, please contact our main hotline at 123-4567."
    
    if any(word in user_lower for word in ['hello', 'hi', 'hey']):
        return "Hello! I can help with delivery, order, or app issues. What seems to be the problem?"
    elif any(word in user_lower for word in delivery_keywords):
        return "I understand you're having delivery concerns. Can you provide your tracking number or order ID?"
    elif any(word in user_lower for word in order_keywords):
        return "I'm sorry about your order issue. Please provide your order number so I can assist you."
    elif any(word in user_lower for word in internet_keywords):
        return "I understand you're experiencing technical difficulties. Have you tried clearing your app cache or reinstalling?"
    elif any(word in user_lower for word in ['thank', 'thanks']):
        return "You're welcome! Is there anything else I can help you with today?"
    elif any(word in user_lower for word in ['bye', 'goodbye']):
        return "Thank you for calling Lazada. Have a great day!"
    else:
        return "Could you please provide more details about your delivery, order, or app issue?"


# ============================================
# ERROR HANDLERS
# ============================================

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


@app.errorhandler(404)
def not_found(e):
    return jsonify({
        'error': 'Not found',
        'message': 'The requested resource was not found.'
    }), 404


# ============================================
# APPLICATION STARTUP
# ============================================

if __name__ == '__main__':
    # Create tables if they don't exist
    app.db.create_all()
    
    print("=" * 60)
    print("CallSim - Lazada Customer Support Simulator")
    print("=" * 60)
    print("Frontend: http://localhost:5500")
    print("API Docs: http://localhost:5000/apidocs")
    print("API: http://localhost:5000/api/v1/")
    print("Vertex AI: " + ("Configured" if GOOGLE_CLOUD_PROJECT else "Not Configured"))
    print("=" * 60)
    
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=True
    )
