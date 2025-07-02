#!/usr/bin/env python3
"""
Reset password for a test user to enable JWT testing.
"""

import os
from werkzeug.security import generate_password_hash
import psycopg2

def reset_user_password(email: str, new_password: str):
    """Reset a user's password in the database."""
    
    # Get database connection
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        return False
    
    try:
        # Connect to database
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT id, email FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        if not user:
            print(f"❌ User {email} not found in database")
            return False
        
        user_id, user_email = user
        print(f"✓ Found user: {user_email} (ID: {user_id})")
        
        # Generate new password hash
        password_hash = generate_password_hash(new_password)
        
        # Update password
        cursor.execute(
            "UPDATE users SET password_hash = %s WHERE email = %s",
            (password_hash, email)
        )
        
        conn.commit()
        print(f"✓ Password updated for {email}")
        print(f"  New password: {new_password}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating password: {e}")
        return False

def main():
    """Reset password for existing test users."""
    print("=== Reset Test User Password ===\n")
    
    # Reset password for existing user
    email = "jindal.siddharth1@gmail.com"
    new_password = "test123"
    
    print(f"Resetting password for: {email}")
    
    if reset_user_password(email, new_password):
        print(f"\n🎉 SUCCESS!")
        print(f"You can now test JWT authentication with:")
        print(f"  Email: {email}")
        print(f"  Password: {new_password}")
        print(f"\nTest steps:")
        print(f"1. Go to http://localhost:5000/login")
        print(f"2. Login with the credentials above")
        print(f"3. Check browser DevTools > Application > Cookies")
        print(f"4. Look for smriti_access_token and smriti_refresh_token")
        print(f"5. Navigate to /journal - should work without redirect")
    else:
        print("\n❌ Password reset failed")

if __name__ == "__main__":
    main()