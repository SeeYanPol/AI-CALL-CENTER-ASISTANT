"""
Database initialization and migration script
Run this to set up the database for the first time
"""
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from database import db_config
from models import Base, User, UserRole
from auth import create_user
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_database():
    """Initialize database and create tables"""
    logger.info("Initializing database...")
    
    try:
        # Initialize engine
        db_config.init_engine()
        
        # Create all tables
        db_config.create_all()
        
        logger.info("✓ Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to create database tables: {str(e)}")
        return False


def create_admin_user():
    """Create default admin user if it doesn't exist"""
    logger.info("Creating default admin user...")
    
    try:
        admin_email = os.getenv('ADMIN_EMAIL', 'admin@callsim.com')
        admin_password = os.getenv('ADMIN_PASSWORD', 'Admin123!')
        
        # Check if admin exists
        session = db_config.get_session()
        existing_admin = session.query(User).filter_by(email=admin_email).first()
        
        if existing_admin:
            logger.info(f"✓ Admin user already exists: {admin_email}")
            session.close()
            return True
        
        session.close()
        
        # Create admin user
        admin_user = create_user(
            email=admin_email,
            password=admin_password,
            full_name='System Administrator',
            role='admin'
        )
        
        logger.info(f"✓ Admin user created: {admin_email}")
        logger.warning(f"⚠ Default password: {admin_password}")
        logger.warning("⚠ CHANGE THIS PASSWORD IMMEDIATELY IN PRODUCTION!")
        
        return True
    except Exception as e:
        logger.error(f"✗ Failed to create admin user: {str(e)}")
        return False


def verify_database():
    """Verify database connection and tables"""
    logger.info("Verifying database...")
    
    try:
        # Health check
        if not db_config.health_check():
            logger.error("✗ Database health check failed")
            return False
        
        # Check tables
        session = db_config.get_session()
        user_count = session.query(User).count()
        session.close()
        
        logger.info(f"✓ Database verified. Users: {user_count}")
        return True
    except Exception as e:
        logger.error(f"✗ Database verification failed: {str(e)}")
        return False


def main():
    """Main initialization function"""
    logger.info("=" * 60)
    logger.info("CallSim Database Initialization")
    logger.info("=" * 60)
    
    steps = [
        ("Initializing database", init_database),
        ("Creating admin user", create_admin_user),
        ("Verifying database", verify_database),
    ]
    
    for step_name, step_func in steps:
        logger.info(f"\n{step_name}...")
        if not step_func():
            logger.error(f"\n✗ Initialization failed at: {step_name}")
            sys.exit(1)
    
    logger.info("\n" + "=" * 60)
    logger.info("✓ Database initialization completed successfully!")
    logger.info("=" * 60)
    logger.info("\nNext steps:")
    logger.info("1. Change the default admin password")
    logger.info("2. Configure environment variables in .env")
    logger.info("3. Start the application: python app_v2.py")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
