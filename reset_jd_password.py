#!/usr/bin/env python3
"""
Reset password for JD (jdoninternet@gmail.com) to enable login testing.
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash

def reset_jd_password():
    """Reset JD's password to a known value."""
    
    # Get database URL
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("Error: DATABASE_URL environment variable not set")
        return False
    
    # Create database connection
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    
    try:
        with Session() as session:
            # Set a simple password for testing
            new_password = "test123"
            password_hash = generate_password_hash(new_password)
            
            # Update the password
            query = text("""
                UPDATE users 
                SET password_hash = :password_hash, updated_at = NOW()
                WHERE email = 'jdoninternet@gmail.com'
            """)
            
            result = session.execute(query, {"password_hash": password_hash})
            session.commit()
            
            if result.rowcount > 0:
                print(f"✅ Password reset successful for jdoninternet@gmail.com")
                print(f"📧 Email: jdoninternet@gmail.com")
                print(f"🔑 Password: {new_password}")
                return True
            else:
                print("❌ No user found with email jdoninternet@gmail.com")
                return False
                
    except Exception as e:
        print(f"❌ Error resetting password: {e}")
        return False

if __name__ == "__main__":
    reset_jd_password()