#!/usr/bin/env python3
"""
Script to update the default max_tokens setting to 4000.
This fixes the issue where images are truncated due to low token limits.
"""

from database import SessionLocal
from sqlalchemy import text
import os

def update_max_tokens():
    """Update ai_max_tokens to 4000 in settings key-value store."""
    db_path = os.path.join(os.path.dirname(__file__), "contextpilot.db")
    print(f"Using database: {db_path}")
    
    session = SessionLocal()
    try:
        # Check current value
        result = session.execute(
            text("SELECT value FROM settings WHERE key = 'ai_max_tokens'")
        ).scalar()
        
        if result:
            current = int(result)
            print(f"Current ai_max_tokens: {current}")
            
            if current < 4000:
                # Update to 4000
                session.execute(
                    text("UPDATE settings SET value = '4000' WHERE key = 'ai_max_tokens'")
                )
                session.commit()
                print(f"✅ Updated ai_max_tokens: {current} → 4000")
            else:
                print(f"✅ ai_max_tokens already set to {current} (no update needed)")
        else:
            # Insert new setting
            session.execute(
                text("INSERT INTO settings (key, value) VALUES ('ai_max_tokens', '4000')")
            )
            session.commit()
            print("✅ Created ai_max_tokens setting: 4000")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    update_max_tokens()
