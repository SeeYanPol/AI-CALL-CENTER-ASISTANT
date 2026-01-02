"""
Database configuration and initialization (SQLite for development)
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from contextlib import contextmanager
from models import Base
import logging

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database configuration manager"""
    
    def __init__(self, database_url=None):
        # Use SQLite by default for simplicity
        self.database_url = database_url or os.getenv(
            'DATABASE_URL',
            'sqlite:///callsim.db'
        )
        
        self.engine = None
        self.session_factory = None
        self.Session = None
    
    def init_engine(self):
        """Initialize database engine"""
        # SQLite specific settings
        connect_args = {}
        if self.database_url.startswith('sqlite'):
            connect_args = {'check_same_thread': False}
        
        self.engine = create_engine(
            self.database_url,
            connect_args=connect_args,
            echo=os.getenv('SQL_ECHO', 'False').lower() == 'true'
        )
        
        self.session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.session_factory)
        
        logger.info("Database engine initialized")
        return self.engine
    
    def create_all(self):
        """Create all database tables"""
        if not self.engine:
            self.init_engine()
        
        Base.metadata.create_all(self.engine)
        logger.info("Database tables created")
    
    def drop_all(self):
        """Drop all database tables (use with caution!)"""
        if not self.engine:
            self.init_engine()
        
        Base.metadata.drop_all(self.engine)
        logger.warning("All database tables dropped")
    
    def get_session(self):
        """Get a new database session"""
        if not self.Session:
            self.init_engine()
        return self.Session()
    
    def remove_session(self):
        """Remove the current scoped session"""
        if self.Session:
            self.Session.remove()
    
    @contextmanager
    def session_scope(self):
        """Provide a transactional scope for database operations"""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {str(e)}")
            raise
        finally:
            session.close()
    
    def health_check(self):
        """Check database connection health"""
        try:
            from sqlalchemy import text
            with self.session_scope() as session:
                session.execute(text('SELECT 1'))
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return False


# Global database instance
db_config = DatabaseConfig()


def init_db(app=None):
    """Initialize database for Flask app"""
    if app:
        # Store database config in app
        app.db = db_config
    
    db_config.init_engine()
    return db_config


def get_db_session():
    """Get database session (for use in Flask context)"""
    return db_config.get_session()
