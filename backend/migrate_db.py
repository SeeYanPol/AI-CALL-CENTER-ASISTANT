"""
Database Migration: Add Recording Fields
Run this after updating to Lazada CallSim version
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_db_session
from sqlalchemy import text

def migrate_database():
    """Add recording fields to existing database"""
    print("=" * 60)
    print("Lazada CallSim - Database Migration")
    print("=" * 60)
    
    db = get_db_session()
    
    try:
        # Check if columns already exist
        result = db.execute(text("PRAGMA table_info(call_sessions)"))
        columns = [row[1] for row in result]
        
        # Add recording_directory if not exists
        if 'recording_directory' not in columns:
            print("✅ Adding recording_directory to call_sessions...")
            db.execute(text(
                "ALTER TABLE call_sessions ADD COLUMN recording_directory VARCHAR(500)"
            ))
            db.commit()
        else:
            print("ℹ️  recording_directory already exists in call_sessions")
        
        # Check chat_messages table
        result = db.execute(text("PRAGMA table_info(chat_messages)"))
        columns = [row[1] for row in result]
        
        # Add recording_path if not exists
        if 'recording_path' not in columns:
            print("✅ Adding recording_path to chat_messages...")
            db.execute(text(
                "ALTER TABLE chat_messages ADD COLUMN recording_path VARCHAR(500)"
            ))
            db.commit()
        else:
            print("ℹ️  recording_path already exists in chat_messages")
        
        print("\n" + "=" * 60)
        print("✅ Migration completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()
    
    return True

if __name__ == '__main__':
    success = migrate_database()
    sys.exit(0 if success else 1)
