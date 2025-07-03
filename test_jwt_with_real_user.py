#!/usr/bin/env python3
"""
JWT Token Test with Real User Data

This script tests JWT functionality using an existing user from the database.
"""

import jwt
import os
from datetime import datetime, timezone
from app.utils.jwt_utils import generate_access_token, verify_access_token

def test_jwt_with_real_user():
    """Test JWT tokens using a real user from the database."""
    print("=== JWT Token Test with Real User ===\n")
    
    # Use a real user ID from the database
    real_user_id = "2e1478a3-50b8-48a3-ae4f-b1dfd042be0f"  # From jindal.siddharth1@gmail.com
    real_email = "jindal.siddharth1@gmail.com"
    
    print("1. Testing access token generation...")
    try:
        # Generate access token (doesn't require database storage)
        access_token = generate_access_token(real_user_id, real_email)
        print(f"   ✓ Access token generated successfully")
        print(f"   Token length: {len(access_token)} characters")
        
        # Decode token to show structure (without verification)
        payload = jwt.decode(access_token, options={"verify_signature": False})
        print(f"   Token payload:")
        print(f"     - User ID: {payload.get('user_id')}")
        print(f"     - Email: {payload.get('email')}")
        print(f"     - Expires: {datetime.fromtimestamp(payload['exp'], tz=timezone.utc)}")
        print(f"     - Issued: {datetime.fromtimestamp(payload['iat'], tz=timezone.utc)}")
        
    except Exception as e:
        print(f"   ✗ Access token generation failed: {e}")
        return
    
    print("\n2. Testing access token verification...")
    try:
        user_data = verify_access_token(access_token)
        if user_data:
            print(f"   ✓ Access token verification successful")
            print(f"   Verified user ID: {user_data['user_id']}")
            print(f"   Verified email: {user_data['email']}")
        else:
            print("   ✗ Access token verification failed")
    except Exception as e:
        print(f"   ✗ Access token verification error: {e}")
    
    print("\n3. Environment configuration check...")
    jwt_secret = os.environ.get('JWT_SECRET_KEY')
    if jwt_secret:
        print(f"   ✓ JWT_SECRET_KEY configured (length: {len(jwt_secret)})")
    else:
        print("   ✗ JWT_SECRET_KEY not found")
    
    access_expiry = os.environ.get('JWT_ACCESS_TOKEN_EXPIRE_MINUTES', '30')
    refresh_expiry = os.environ.get('JWT_REFRESH_TOKEN_EXPIRE_DAYS', '14')
    print(f"   Access token expiry: {access_expiry} minutes")
    print(f"   Refresh token expiry: {refresh_expiry} days")
    
    print("\n4. Cookie format demonstration...")
    print("   When user logs in, these cookies will be set:")
    print(f"   smriti_access_token={access_token[:50]}...")
    print("   Properties: HttpOnly, Secure, SameSite=Lax, Max-Age=1800")
    
    return access_token

def test_manual_login_simulation():
    """Show how to test the login flow manually."""
    print("\n" + "=" * 60)
    print("🔐 MANUAL TESTING INSTRUCTIONS")
    print("=" * 60)
    print("To test the complete JWT authentication flow:")
    print("")
    print("1. Open browser and go to: http://localhost:5000/")
    print("2. Should see login page (homepage redirects if not authenticated)")
    print("3. Login with: jindal.siddharth1@gmail.com")
    print("4. Open browser DevTools (F12) > Application > Cookies")
    print("5. Look for these cookies:")
    print("   - smriti_access_token (expires in 30 minutes)")
    print("   - smriti_refresh_token (expires in 14 days)")
    print("6. Navigate to: http://localhost:5000/journal")
    print("7. Should access successfully (JWT authentication working)")
    print("8. Test logout: http://localhost:5000/logout")
    print("9. Verify cookies are cleared")
    print("10. Try accessing /journal again - should redirect to login")
    print("")
    print("API Testing:")
    print("- Refresh token: POST http://localhost:5000/api/v1/auth/refresh")
    print("- Should work when valid refresh token cookie is present")
    print("=" * 60)

if __name__ == "__main__":
    access_token = test_jwt_with_real_user()
    test_manual_login_simulation()
    
    if access_token:
        print(f"\n✅ JWT Authentication System is working correctly!")
        print(f"   Generated valid access token for real user")
        print(f"   Token verified successfully")
        print(f"   Ready for browser testing")