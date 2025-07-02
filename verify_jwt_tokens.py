#!/usr/bin/env python3
"""
JWT Token Verification Script

This script demonstrates how to test JWT tokens manually by:
1. Generating test tokens 
2. Verifying their structure and expiration
3. Testing token refresh functionality
"""

import jwt
import os
from datetime import datetime, timezone
from app.utils.jwt_utils import generate_access_token, generate_refresh_token, verify_access_token, verify_refresh_token

def demo_jwt_functionality():
    """Demonstrate JWT token generation and verification."""
    print("=== JWT Token Verification Demo ===\n")
    
    # Test data
    test_user_id = "123e4567-e89b-12d3-a456-426614174000"
    test_email = "test@example.com"
    
    print("1. Generating JWT tokens...")
    try:
        # Generate tokens
        access_token = generate_access_token(test_user_id, test_email)
        refresh_token = generate_refresh_token(test_user_id)
        
        print(f"   ✓ Access token generated: {access_token[:50]}...")
        print(f"   ✓ Refresh token generated: {refresh_token[:50]}...")
        
        # Decode tokens to show structure (without verification for demo)
        access_payload = jwt.decode(access_token, options={"verify_signature": False})
        print(f"   Access token payload: {access_payload}")
        
        # Verify access token expiration
        exp_time = datetime.fromtimestamp(access_payload['exp'], tz=timezone.utc)
        print(f"   Access token expires: {exp_time}")
        
    except Exception as e:
        print(f"   ✗ Token generation failed: {e}")
        return
    
    print("\n2. Verifying access token...")
    try:
        user_data = verify_access_token(access_token)
        if user_data:
            print(f"   ✓ Access token valid")
            print(f"   User ID: {user_data['user_id']}")
            print(f"   Email: {user_data['email']}")
        else:
            print("   ✗ Access token invalid")
    except Exception as e:
        print(f"   ✗ Access token verification failed: {e}")
    
    print("\n3. Verifying refresh token...")
    try:
        user_id = verify_refresh_token(refresh_token)
        if user_id:
            print(f"   ✓ Refresh token valid for user: {user_id}")
        else:
            print("   ✗ Refresh token invalid")
    except Exception as e:
        print(f"   ✗ Refresh token verification failed: {e}")
    
    print("\n4. Environment check...")
    jwt_secret = os.environ.get('JWT_SECRET_KEY')
    if jwt_secret:
        print(f"   ✓ JWT_SECRET_KEY configured (length: {len(jwt_secret)})")
    else:
        print("   ✗ JWT_SECRET_KEY not found in environment")
    
    access_expiry = os.environ.get('JWT_ACCESS_TOKEN_EXPIRE_MINUTES', '30')
    refresh_expiry = os.environ.get('JWT_REFRESH_TOKEN_EXPIRE_DAYS', '14')
    print(f"   Access token expiry: {access_expiry} minutes")
    print(f"   Refresh token expiry: {refresh_expiry} days")

def test_cookie_format():
    """Test the cookie format that would be set by the application."""
    print("\n5. Testing cookie format...")
    
    # Simulate cookie setting
    test_user_id = "123e4567-e89b-12d3-a456-426614174000"
    test_email = "test@example.com"
    
    access_token = generate_access_token(test_user_id, test_email)
    refresh_token = generate_refresh_token(test_user_id)
    
    print(f"   Cookie: smriti_access_token={access_token}; HttpOnly; Secure; SameSite=Lax; Max-Age=1800")
    print(f"   Cookie: smriti_refresh_token={refresh_token}; HttpOnly; Secure; SameSite=Lax; Max-Age=1209600")

if __name__ == "__main__":
    demo_jwt_functionality()
    test_cookie_format()
    
    print("\n" + "=" * 60)
    print("🔐 JWT AUTHENTICATION SYSTEM READY")
    print("=" * 60)
    print("To test in browser:")
    print("1. Open http://localhost:5000/login")
    print("2. Login with existing user credentials")
    print("3. Check browser DevTools > Application > Cookies")
    print("4. Verify 'smriti_access_token' and 'smriti_refresh_token' exist")
    print("5. Access http://localhost:5000/journal (should work)")
    print("6. Access http://localhost:5000/logout (should clear cookies)")
    print("=" * 60)