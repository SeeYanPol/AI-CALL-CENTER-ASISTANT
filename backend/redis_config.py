"""
Redis configuration and session management
"""
import os
import json
import redis
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class RedisConfig:
    """Redis configuration manager"""
    
    def __init__(self):
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self.session_prefix = 'session:'
        self.cache_prefix = 'cache:'
        self.default_ttl = int(os.getenv('REDIS_TTL', 3600))  # 1 hour default
        
        self.client = None
    
    def init_redis(self):
        """Initialize Redis connection"""
        try:
            self.client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
                health_check_interval=30
            )
            # Test connection
            self.client.ping()
            logger.info("Redis connection established")
            return self.client
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise
    
    def get_client(self):
        """Get Redis client"""
        if not self.client:
            self.init_redis()
        return self.client
    
    def health_check(self):
        """Check Redis connection health"""
        try:
            client = self.get_client()
            client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {str(e)}")
            return False
    
    # Session methods
    def save_session(self, session_id, data, ttl=None):
        """Save session data to Redis"""
        try:
            client = self.get_client()
            key = f"{self.session_prefix}{session_id}"
            serialized_data = json.dumps(data)
            
            if ttl:
                client.setex(key, ttl, serialized_data)
            else:
                client.setex(key, self.default_ttl, serialized_data)
            
            return True
        except Exception as e:
            logger.error(f"Failed to save session {session_id}: {str(e)}")
            return False
    
    def get_session(self, session_id):
        """Retrieve session data from Redis"""
        try:
            client = self.get_client()
            key = f"{self.session_prefix}{session_id}"
            data = client.get(key)
            
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {str(e)}")
            return None
    
    def update_session(self, session_id, data, ttl=None):
        """Update existing session data"""
        return self.save_session(session_id, data, ttl)
    
    def delete_session(self, session_id):
        """Delete session from Redis"""
        try:
            client = self.get_client()
            key = f"{self.session_prefix}{session_id}"
            client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {str(e)}")
            return False
    
    def extend_session(self, session_id, ttl=None):
        """Extend session TTL"""
        try:
            client = self.get_client()
            key = f"{self.session_prefix}{session_id}"
            ttl = ttl or self.default_ttl
            client.expire(key, ttl)
            return True
        except Exception as e:
            logger.error(f"Failed to extend session {session_id}: {str(e)}")
            return False
    
    def get_all_sessions(self, user_id=None):
        """Get all active sessions (optionally filtered by user_id)"""
        try:
            client = self.get_client()
            pattern = f"{self.session_prefix}*"
            sessions = []
            
            for key in client.scan_iter(match=pattern):
                data = client.get(key)
                if data:
                    session_data = json.loads(data)
                    if user_id is None or session_data.get('user_id') == user_id:
                        sessions.append(session_data)
            
            return sessions
        except Exception as e:
            logger.error(f"Failed to get all sessions: {str(e)}")
            return []
    
    # Cache methods
    def cache_set(self, key, value, ttl=None):
        """Set a cache value"""
        try:
            client = self.get_client()
            cache_key = f"{self.cache_prefix}{key}"
            serialized_value = json.dumps(value)
            
            if ttl:
                client.setex(cache_key, ttl, serialized_value)
            else:
                client.setex(cache_key, self.default_ttl, serialized_value)
            
            return True
        except Exception as e:
            logger.error(f"Failed to set cache {key}: {str(e)}")
            return False
    
    def cache_get(self, key):
        """Get a cache value"""
        try:
            client = self.get_client()
            cache_key = f"{self.cache_prefix}{key}"
            value = client.get(cache_key)
            
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Failed to get cache {key}: {str(e)}")
            return None
    
    def cache_delete(self, key):
        """Delete a cache value"""
        try:
            client = self.get_client()
            cache_key = f"{self.cache_prefix}{key}"
            client.delete(cache_key)
            return True
        except Exception as e:
            logger.error(f"Failed to delete cache {key}: {str(e)}")
            return False
    
    def cache_exists(self, key):
        """Check if cache key exists"""
        try:
            client = self.get_client()
            cache_key = f"{self.cache_prefix}{key}"
            return client.exists(cache_key) > 0
        except Exception as e:
            logger.error(f"Failed to check cache {key}: {str(e)}")
            return False
    
    # Rate limiting methods
    def check_rate_limit(self, identifier, limit, window):
        """
        Check if rate limit is exceeded
        
        Args:
            identifier: Unique identifier (user_id, ip, etc.)
            limit: Maximum number of requests
            window: Time window in seconds
        
        Returns:
            tuple: (allowed: bool, remaining: int, reset_time: int)
        """
        try:
            client = self.get_client()
            key = f"ratelimit:{identifier}"
            
            # Use Redis pipeline for atomic operations
            pipe = client.pipeline()
            now = int(datetime.now().timestamp())
            window_start = now - window
            
            # Remove old entries
            pipe.zremrangebyscore(key, 0, window_start)
            # Count entries in current window
            pipe.zcard(key)
            # Add current request
            pipe.zadd(key, {str(now): now})
            # Set expiry
            pipe.expire(key, window)
            
            results = pipe.execute()
            current_count = results[1]
            
            allowed = current_count < limit
            remaining = max(0, limit - current_count - 1)
            reset_time = now + window
            
            return allowed, remaining, reset_time
        except Exception as e:
            logger.error(f"Rate limit check failed: {str(e)}")
            # Fail open - allow request if Redis is down
            return True, limit, 0
    
    def flush_all(self):
        """Flush all Redis data (use with caution!)"""
        try:
            client = self.get_client()
            client.flushdb()
            logger.warning("Redis database flushed")
            return True
        except Exception as e:
            logger.error(f"Failed to flush Redis: {str(e)}")
            return False


# Global Redis instance
redis_config = RedisConfig()


def init_redis(app=None):
    """Initialize Redis for Flask app"""
    if app:
        app.redis = redis_config
    
    redis_config.init_redis()
    return redis_config


def get_redis_client():
    """Get Redis client (for use in Flask context)"""
    return redis_config.get_client()
