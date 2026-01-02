"""
Celery tasks for async operations
"""
import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

# Initialize Celery
celery_app = Celery(
    'callsim_tasks',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/1'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/2')
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
)


@celery_app.task(name='tasks.generate_tts')
def generate_tts_async(text, lang='en'):
    """
    Generate TTS audio asynchronously
    
    Args:
        text: Text to convert to speech
        lang: Language code
        
    Returns:
        dict: Audio data and metadata
    """
    from gtts import gTTS
    import io
    import base64
    
    try:
        tts = gTTS(text=text, lang=lang, slow=False)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        
        # Encode as base64 for transport
        audio_data = base64.b64encode(audio_buffer.getvalue()).decode('utf-8')
        
        return {
            'status': 'success',
            'audio_data': audio_data,
            'text': text,
            'lang': lang
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }


@celery_app.task(name='tasks.generate_ai_response')
def generate_ai_response_async(message, session_id=None, system_prompt=None):
    """
    Generate AI response asynchronously
    
    Args:
        message: User message
        session_id: Optional session ID for context
        system_prompt: Optional custom system prompt
        
    Returns:
        dict: AI response and metadata
    """
    import openai
    from database import get_db_session
    from models import ChatMessage
    
    openai.api_key = os.getenv('OPENAI_API_KEY')
    
    try:
        messages = []
        
        # Load session history if provided
        if session_id:
            db_session = get_db_session()
            history = db_session.query(ChatMessage).filter_by(
                session_id=session_id
            ).order_by(ChatMessage.timestamp).all()
            
            messages = [{'role': msg.role, 'content': msg.content} for msg in history]
            db_session.close()
        
        # Add system prompt
        if system_prompt:
            messages.insert(0, {'role': 'system', 'content': system_prompt})
        
        # Add user message
        messages.append({'role': 'user', 'content': message})
        
        # Generate response
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=150,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content.strip()
        tokens_used = response.usage.total_tokens
        
        return {
            'status': 'success',
            'response': ai_response,
            'tokens_used': tokens_used
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'response': "I apologize, I'm having trouble processing that right now."
        }


@celery_app.task(name='tasks.cleanup_old_sessions')
def cleanup_old_sessions():
    """
    Cleanup old inactive sessions (run periodically)
    """
    from datetime import datetime, timedelta
    from database import get_db_session
    from models import CallSession
    
    db_session = get_db_session()
    
    try:
        # Delete sessions older than 7 days
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        
        old_sessions = db_session.query(CallSession).filter(
            CallSession.started_at < cutoff_date,
            CallSession.status == 'ended'
        ).all()
        
        count = len(old_sessions)
        
        for session in old_sessions:
            db_session.delete(session)
        
        db_session.commit()
        
        return {
            'status': 'success',
            'deleted_count': count
        }
    except Exception as e:
        db_session.rollback()
        return {
            'status': 'error',
            'error': str(e)
        }
    finally:
        db_session.close()


@celery_app.task(name='tasks.send_email_verification')
def send_email_verification(user_id, email):
    """
    Send email verification (placeholder - implement with your email service)
    
    Args:
        user_id: User ID
        email: Email address
    """
    # Implement with SendGrid, AWS SES, etc.
    print(f"Sending verification email to {email} for user {user_id}")
    return {'status': 'success', 'email': email}


# Periodic tasks configuration
celery_app.conf.beat_schedule = {
    'cleanup-old-sessions': {
        'task': 'tasks.cleanup_old_sessions',
        'schedule': 86400.0,  # Run daily
    },
}
