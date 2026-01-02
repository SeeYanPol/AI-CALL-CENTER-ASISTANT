"""
Database models for CallSim AI Call Center
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, ForeignKey, Enum, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import enum

Base = declarative_base()


class UserRole(enum.Enum):
    """User role enumeration"""
    ADMIN = "admin"
    TRAINER = "trainer"
    TRAINEE = "trainee"


class User(Base):
    """User model for authentication and authorization"""
    __tablename__ = 'users'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.TRAINEE, nullable=False)
    
    # Status fields
    is_active = Column(Boolean, default=True, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime)
    
    # Relationships
    sessions = relationship('CallSession', back_populates='user', cascade='all, delete-orphan')
    api_keys = relationship('UserAPIKey', back_populates='user', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set user password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self, include_sensitive=False):
        """Convert user to dictionary"""
        data = {
            'id': self.id,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role.value,
            'is_active': self.is_active,
            'email_verified': self.email_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
        return data
    
    def __repr__(self):
        return f'<User {self.email}>'


class UserAPIKey(Base):
    """API keys for user authentication"""
    __tablename__ = 'user_api_keys'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    key_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)  # Friendly name for the key
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_used = Column(DateTime)
    expires_at = Column(DateTime)
    
    # Relationship
    user = relationship('User', back_populates='api_keys')
    
    def __repr__(self):
        return f'<UserAPIKey {self.name} for user {self.user_id}>'


class CallSession(Base):
    """Call session model for tracking user calls"""
    __tablename__ = 'call_sessions'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # Session data
    session_token = Column(String(255), nullable=False, unique=True, index=True)
    caller_info = Column(JSON)
    
    # Status
    status = Column(String(20), default='active')  # active, ended, abandoned
    
    # Metrics
    duration_seconds = Column(Integer, default=0)
    message_count = Column(Integer, default=0)
    
    # Performance scores (0-100)
    overall_score = Column(Float)
    empathy_score = Column(Float)
    clarity_score = Column(Float)
    problem_solving_score = Column(Float)
    
    # Recording storage
    recording_directory = Column(String(500))  # Directory path for all recordings in this session
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at = Column(DateTime)
    
    # Relationships
    user = relationship('User', back_populates='sessions')
    messages = relationship('ChatMessage', back_populates='session', cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert session to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'status': self.status,
            'caller_info': self.caller_info,
            'duration_seconds': self.duration_seconds,
            'message_count': self.message_count,
            'overall_score': self.overall_score,
            'empathy_score': self.empathy_score,
            'clarity_score': self.clarity_score,
            'problem_solving_score': self.problem_solving_score,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None
        }
    
    def __repr__(self):
        return f'<CallSession {self.id} for user {self.user_id}>'


class ChatMessage(Base):
    """Chat messages within a call session"""
    __tablename__ = 'chat_messages'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey('call_sessions.id', ondelete='CASCADE'), nullable=False)
    
    # Message data
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    speaker = Column(String(50))  # Agent, Caller
    
    # Recording path for evaluation
    recording_path = Column(String(500))  # Local path to audio recording
    
    # Metadata
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    tokens_used = Column(Integer)  # For tracking API costs
    
    # Relationship
    session = relationship('CallSession', back_populates='messages')
    
    def to_dict(self):
        """Convert message to dictionary"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'role': self.role,
            'content': self.content,
            'speaker': self.speaker,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'tokens_used': self.tokens_used
        }
    
    def __repr__(self):
        return f'<ChatMessage {self.id} in session {self.session_id}>'


class AuditLog(Base):
    """Audit log for security and compliance"""
    __tablename__ = 'audit_logs'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id', ondelete='SET NULL'))
    
    # Event data
    event_type = Column(String(50), nullable=False, index=True)  # login, logout, api_call, etc.
    resource = Column(String(100))  # What was accessed
    action = Column(String(50))  # What action was performed
    
    # Details
    ip_address = Column(String(45))
    user_agent = Column(String(255))
    status_code = Column(Integer)
    error_message = Column(Text)
    event_metadata = Column(JSON)
    
    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self):
        return f'<AuditLog {self.event_type} by user {self.user_id}>'
