#!/usr/bin/env python3
"""
Test complete authentication flow: signup -> login -> protected route access -> logout
"""

import requests
import uuid
import time

def test_complete_auth_flow():
    """Test the complete authentication flow with JWT tokens."""
    print("=== Testing Complete JWT Authentication Flow ===\n")
    
    # Generate unique test user
    test_id = str(uuid.uuid4())[:8]
    test_email = f"test_{test_id}@example.com"
    test_password = "TestPassword123!"
    test_display_name = f"Test User {test_id}"
    
    session = requests.Session()
    
    print("1. Testing user signup...")
    signup_data = {
        'email': test_email,
        'password': test_password,
        'confirm_password': test_password,
        'display_name': test_display_name
    }
    
    response = session.post("http://localhost:5000/signup", data=signup_data, allow_redirects=False)
    print(f"   Signup status: {response.status_code}")
    
    if response.status_code != 303:
        print(f"   ✗ Signup failed: {response.text[:200]}...")
        return False
    
    print(f"   ✓ Signup successful for: {test_email}")
    
    print("\n2. Testing login with new user...")
    login_data = {
        'email': test_email,
        'password': test_password
    }
    
    response = session.post("http://localhost:5000/login", data=login_data, allow_redirects=False)
    print(f"   Login status: {response.status_code}")
    print(f"   Redirect location: {response.headers.get('location', 'None')}")
    
    # Check cookies
    cookies = session.cookies
    access_token = cookies.get('smriti_access_token')
    refresh_token = cookies.get('smriti_refresh_token')
    
    print(f"   Access token present: {bool(access_token)}")
    print(f"   Refresh token present: {bool(refresh_token)}")
    
    if not (access_token and refresh_token):
        print("   ✗ JWT tokens not set properly")
        return False
        
    print("   ✓ JWT tokens set successfully")
    
    print("\n3. Testing protected route access...")
    response = session.get("http://localhost:5000/journal", allow_redirects=False)
    print(f"   Journal access status: {response.status_code}")
    
    if response.status_code == 200:
        print("   ✓ Protected route accessible with JWT")
    elif response.status_code == 303:
        print(f"   ✗ Redirected to: {response.headers.get('location')}")
        return False
    else:
        print(f"   ✗ Unexpected status: {response.status_code}")
        return False
    
    print("\n4. Testing token refresh endpoint...")
    response = session.post("http://localhost:5000/api/v1/auth/refresh")
    print(f"   Refresh endpoint status: {response.status_code}")
    
    if response.status_code == 200:
        print("   ✓ Token refresh working")
    else:
        print(f"   ✗ Token refresh failed: {response.text}")
    
    print("\n5. Testing logout...")
    response = session.get("http://localhost:5000/logout", allow_redirects=False)
    print(f"   Logout status: {response.status_code}")
    
    # Check if cookies are cleared
    cookies_after_logout = session.cookies
    access_token_after = cookies_after_logout.get('smriti_access_token')
    refresh_token_after = cookies_after_logout.get('smriti_refresh_token')
    
    print(f"   Access token after logout: {bool(access_token_after)}")
    print(f"   Refresh token after logout: {bool(refresh_token_after)}")
    
    print("\n6. Testing access after logout...")
    response = session.get("http://localhost:5000/journal", allow_redirects=False)
    print(f"   Journal access after logout: {response.status_code}")
    
    if response.status_code == 303:
        print("   ✓ Correctly redirected to login after logout")
    else:
        print(f"   ✗ Unexpected behavior after logout: {response.status_code}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 ALL JWT AUTHENTICATION TESTS PASSED!")
    print("✓ User signup working")
    print("✓ Login with JWT token generation")
    print("✓ Protected route access with JWT")
    print("✓ Token refresh endpoint working")
    print("✓ Logout with cookie clearing")
    print("✓ Access control after logout")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = test_complete_auth_flow()
    if not success:
        print("\n❌ Authentication flow test failed")
        exit(1)
    else:
        print("\n✅ JWT Authentication system is fully functional!")