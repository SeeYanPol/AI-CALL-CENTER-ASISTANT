"""
Authentication and authorization utilities
"""
import os
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, g
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    verify_jwt_in_request,
    get_jwt
)
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, UserRole, AuditLog
from database import get_db_session
import logging

logger = logging.getLogger(__name__)


class AuthError(Exception):
    """Authentication error exception"""
    def __init__(self, message, status_code=401):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


def generate_tokens(user_id, role):
    """Generate access and refresh tokens"""
    access_token = create_access_token(
        identity=user_id,
        additional_claims={'role': role},
        expires_delta=timedelta(hours=1)
    )
    refresh_token = create_refresh_token(
        identity=user_id,
        expires_delta=timedelta(days=30)
    )
    return access_token, refresh_token


def hash_api_key(api_key):
    """Hash an API key for storage"""
    return generate_password_hash(api_key)


def verify_api_key(api_key, key_hash):
    """Verify an API key against its hash"""
    return check_password_hash(key_hash, api_key)


def generate_api_key():
    """Generate a secure API key"""
    return secrets.token_urlsafe(32)


def get_current_user():
    """Get current authenticated user from JWT"""
    try:
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        
        db_session = get_db_session()
        user = db_session.query(User).filter_by(id=user_id, is_active=True).first()
        
        if not user:
            raise AuthError('User not found or inactive')
        
        return user
    except Exception as e:
        logger.error(f"Error getting current user: {str(e)}")
        raise AuthError('Invalid or expired token')


def jwt_required_custom(f):
    """Custom JWT required decorator with user loading"""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            user = get_current_user()
            g.current_user = user  # Store in Flask g object
            return f(*args, **kwargs)
        except AuthError as e:
            return jsonify({'error': e.message}), e.status_code
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return jsonify({'error': 'Authentication failed'}), 401
    return decorated


def role_required(*allowed_roles):
    """Decorator to require specific roles"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            try:
                user = get_current_user()
                
                if user.role.value not in allowed_roles:
                    logger.warning(f"User {user.id} attempted unauthorized access. Required: {allowed_roles}, Has: {user.role.value}")
                    return jsonify({
                        'error': 'Forbidden',
                        'message': 'You do not have permission to access this resource'
                    }), 403
                
                g.current_user = user
                return f(*args, **kwargs)
            except AuthError as e:
                return jsonify({'error': e.message}), e.status_code
            except Exception as e:
                logger.error(f"Authorization error: {str(e)}")
                return jsonify({'error': 'Authorization failed'}), 403
        return decorated
    return decorator


def log_audit_event(event_type, resource=None, action=None, user_id=None, status_code=200, error_message=None, event_metadata=None):
    """Log an audit event"""
    try:
        db_session = get_db_session()
        
        # Get user ID from current user if not provided
        if not user_id:
            try:
                user = get_current_user()
                user_id = user.id
            except:
                user_id = None
        
        audit_log = AuditLog(
            user_id=user_id,
            event_type=event_type,
            resource=resource,
            action=action,
            ip_address=request.remote_addr if request else None,
            user_agent=request.headers.get('User-Agent') if request else None,
            status_code=status_code,
            error_message=error_message,
            event_metadata=event_metadata
        )
        
        db_session.add(audit_log)
        db_session.commit()
        db_session.close()
    except Exception as e:
        logger.error(f"Failed to log audit event: {str(e)}")


def require_api_key_or_jwt(f):
    """Decorator that accepts either API key or JWT token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Try JWT first
        jwt_header = request.headers.get('Authorization')
        if jwt_header and jwt_header.startswith('Bearer '):
            try:
                user = get_current_user()
                g.current_user = user
                return f(*args, **kwargs)
            except:
                pass
        
        # Try API key
        api_key = request.headers.get('X-API-Key')
        if api_key:
            db_session = get_db_session()
            try:
                # Check against user API keys
                from models import UserAPIKey
                
                for user_key in db_session.query(UserAPIKey).filter_by(is_active=True).all():
                    if verify_api_key(api_key, user_key.key_hash):
                        # Update last used
                        user_key.last_used = datetime.utcnow()
                        db_session.commit()
                        
                        # Load user
                        user = db_session.query(User).filter_by(id=user_key.user_id, is_active=True).first()
                        if user:
                            g.current_user = user
                            return f(*args, **kwargs)
                
                # Check against master API key (for backward compatibility)
                master_key = os.getenv('API_KEY')
                if master_key and secrets.compare_digest(api_key, master_key):
                    # No user context for master key
                    g.current_user = None
                    return f(*args, **kwargs)
            finally:
                db_session.close()
        
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Valid authentication required (JWT token or API key)'
        }), 401
    return decorated


def optional_auth(f):
    """Decorator for optional authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            user = get_current_user()
            g.current_user = user
        except:
            g.current_user = None
        return f(*args, **kwargs)
    return decorated


def create_user(email, password, full_name, role='trainee'):
    """Create a new user"""
    db_session = get_db_session()
    try:
        # Check if user already exists
        existing_user = db_session.query(User).filter_by(email=email).first()
        if existing_user:
            raise ValueError('User with this email already exists')
        
        # Create user
        user = User(
            email=email,
            full_name=full_name,
            role=UserRole[role.upper()]
        )
        user.set_password(password)
        
        db_session.add(user)
        db_session.commit()
        
        # Get user data before closing session
        user_id = user.id
        user_dict = user.to_dict()
        
        # Log audit event
        log_audit_event(
            event_type='user_registration',
            resource='user',
            action='create',
            user_id=user_id,
            event_metadata={'email': email, 'role': role}
        )
        
        return user_dict
    except Exception as e:
        db_session.rollback()
        raise
    finally:
        db_session.close()


def authenticate_user(email, password):
    """Authenticate user and return tokens"""
    db_session = get_db_session()
    try:
        user = db_session.query(User).filter_by(email=email).first()
        
        if not user:
            log_audit_event(
                event_type='login_failed',
                resource='auth',
                action='login',
                status_code=401,
                error_message='User not found',
                event_metadata={'email': email}
            )
            raise AuthError('Invalid email or password')
        
        if not user.is_active:
            log_audit_event(
                event_type='login_failed',
                resource='auth',
                action='login',
                user_id=user.id,
                status_code=401,
                error_message='User account inactive'
            )
            raise AuthError('Account is inactive')
        
        if not user.check_password(password):
            log_audit_event(
                event_type='login_failed',
                resource='auth',
                action='login',
                user_id=user.id,
                status_code=401,
                error_message='Invalid password'
            )
            raise AuthError('Invalid email or password')
        
        # Update last login
        user.last_login = datetime.utcnow()
        db_session.commit()
        
        # Get user data before closing session
        user_dict = user.to_dict()
        user_id = user.id
        role = user.role.value
        
        # Generate tokens
        access_token, refresh_token = generate_tokens(user_id, role)
        
        # Log successful login
        log_audit_event(
            event_type='login_success',
            resource='auth',
            action='login',
            user_id=user_id,
            event_metadata={'email': email}
        )
        
        return {
            'user': user_dict,
            'access_token': access_token,
            'refresh_token': refresh_token
        }
    finally:
        db_session.close()
