#!/usr/bin/env python3
"""
Debug authentication issue with existing users.
"""

import os
import psycopg2
from werkzeug.security import check_password_hash, generate_password_hash

def debug_authentication():
    """Debug the authentication issue step by step."""
    print("=== Debugging Authentication Issue ===\n")
    
    email = "jindal.siddharth1@gmail.com"
    test_password = "test123"
    
    # Connect to database
    database_url = os.environ.get('DATABASE_URL')
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()
    
    # Get user details
    cursor.execute("SELECT id, email, password_hash FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    
    if not user:
        print(f"❌ User {email} not found")
        return
        
    user_id, user_email, stored_hash = user
    print(f"✓ Found user: {user_email}")
    print(f"  User ID: {user_id}")
    print(f"  Stored hash: {stored_hash}")
    print(f"  Hash length: {len(stored_hash) if stored_hash else 'None'}")
    
    # Test password verification
    print(f"\n🔍 Testing password verification:")
    print(f"  Password to test: '{test_password}'")
    
    if stored_hash:
        # Test with current stored hash
        result = check_password_hash(stored_hash, test_password)
        print(f"  check_password_hash result: {result}")
        
        if not result:
            print(f"  ❌ Password verification failed")
            
            # Generate a new hash and test
            print(f"\n🔧 Generating new hash for comparison:")
            new_hash = generate_password_hash(test_password)
            print(f"  New hash: {new_hash}")
            
            # Test new hash
            new_result = check_password_hash(new_hash, test_password)
            print(f"  New hash verification: {new_result}")
            
            # Compare hash formats
            print(f"\n📊 Hash format analysis:")
            print(f"  Stored hash starts with: {stored_hash[:20]}...")
            print(f"  New hash starts with: {new_hash[:20]}...")
            
            # Update password in database with new hash
            print(f"\n🔄 Updating password hash...")
            cursor.execute("UPDATE users SET password_hash = %s WHERE email = %s", (new_hash, email))
            conn.commit()
            print(f"  ✓ Password hash updated")
            
            # Verify update worked
            cursor.execute("SELECT password_hash FROM users WHERE email = %s", (email,))
            updated_hash = cursor.fetchone()[0]
            final_result = check_password_hash(updated_hash, test_password)
            print(f"  Final verification: {final_result}")
            
        else:
            print(f"  ✓ Password verification successful")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    debug_authentication()