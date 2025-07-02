#!/usr/bin/env python3
"""
Test script to verify JWT authentication system is working properly.

This script tests:
1. User login with email/password
2. JWT token generation
3. Token validation and refresh
4. Protected route access
5. Logout functionality
"""

import requests
import json
import time
from urllib.parse import urljoin

# Configuration
BASE_URL = "http://localhost:5000"
API_BASE_URL = "http://localhost:5000/api/v1"

# Test user credentials (you'll need to use a real user from your database)
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpassword123"

def test_login_flow():
    """Test the complete login flow with JWT tokens."""
    print("=== Testing JWT Authentication System ===\n")
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    print("1. Testing login page access...")
    try:
        response = session.get(f"{BASE_URL}/login")
        print(f"   ✓ Login page accessible (Status: {response.status_code})")
    except Exception as e:
        print(f"   ✗ Login page failed: {e}")
        return False
    
    print("2. Testing user authentication...")
    try:
        # Attempt login
        login_data = {
            'email': TEST_EMAIL,
            'password': TEST_PASSWORD
        }
        
        response = session.post(f"{BASE_URL}/login", data=login_data, allow_redirects=False)
        print(f"   Login response status: {response.status_code}")
        
        # Check if we got redirected (successful login)
        if response.status_code == 303:
            print("   ✓ Login successful - got redirect")
            
            # Check if JWT cookies are set
            cookies = session.cookies
            access_token = cookies.get('smriti_access_token')
            refresh_token = cookies.get('smriti_refresh_token')
            
            if access_token and refresh_token:
                print(f"   ✓ JWT tokens set in cookies")
                print(f"     - Access token length: {len(access_token)}")
                print(f"     - Refresh token length: {len(refresh_token)}")
                return session, access_token, refresh_token
            else:
                print("   ✗ JWT tokens not found in cookies")
                return False
        else:
            print(f"   ✗ Login failed - unexpected status code: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"   ✗ Login request failed: {e}")
        return False

def test_protected_route_access(session):
    """Test accessing protected routes with JWT tokens."""
    print("\n3. Testing protected route access...")
    try:
        response = session.get(f"{BASE_URL}/journal", allow_redirects=False)
        
        if response.status_code == 200:
            print("   ✓ Protected route accessible with JWT tokens")
            return True
        elif response.status_code == 303:
            print("   ✗ Got redirected - JWT validation might have failed")
            return False
        else:
            print(f"   ✗ Unexpected response: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ✗ Protected route test failed: {e}")
        return False

def test_token_refresh(access_token, refresh_token):
    """Test the token refresh endpoint."""
    print("\n4. Testing token refresh endpoint...")
    try:
        # Test refresh endpoint
        headers = {'Content-Type': 'application/json'}
        cookies = {
            'smriti_access_token': access_token,
            'smriti_refresh_token': refresh_token
        }
        
        response = requests.post(
            f"{API_BASE_URL}/auth/refresh",
            headers=headers,
            cookies=cookies
        )
        
        if response.status_code == 200:
            print("   ✓ Token refresh endpoint accessible")
            
            # Check if new access token is in response cookies
            new_access_token = None
            for cookie in response.cookies:
                if cookie.name == 'smriti_access_token':
                    new_access_token = cookie.value
                    break
            
            if new_access_token and new_access_token != access_token:
                print("   ✓ New access token generated successfully")
                return True
            else:
                print("   ✗ New access token not found or same as old token")
                return False
        else:
            print(f"   ✗ Token refresh failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ✗ Token refresh test failed: {e}")
        return False

def test_logout(session):
    """Test logout functionality."""
    print("\n5. Testing logout functionality...")
    try:
        response = session.get(f"{BASE_URL}/logout", allow_redirects=False)
        
        if response.status_code == 303:
            print("   ✓ Logout successful - got redirect")
            
            # Check if JWT cookies are cleared
            cookies = session.cookies
            access_token = cookies.get('smriti_access_token')
            refresh_token = cookies.get('smriti_refresh_token')
            
            if not access_token and not refresh_token:
                print("   ✓ JWT cookies cleared successfully")
                return True
            else:
                print("   ✗ JWT cookies not properly cleared")
                return False
        else:
            print(f"   ✗ Logout failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ✗ Logout test failed: {e}")
        return False

def test_homepage_redirect():
    """Test homepage redirects for authenticated users."""
    print("\n6. Testing homepage behavior after logout...")
    try:
        # Create new session (no cookies)
        new_session = requests.Session()
        response = new_session.get(f"{BASE_URL}/", allow_redirects=False)
        
        if response.status_code == 200:
            print("   ✓ Homepage shows login page for unauthenticated users")
            return True
        else:
            print(f"   ✗ Unexpected homepage behavior: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ✗ Homepage test failed: {e}")
        return False

def main():
    """Run all JWT authentication tests."""
    print("Starting JWT Authentication Tests...")
    print(f"Testing against: {BASE_URL}")
    print(f"API Base: {API_BASE_URL}")
    print(f"Test credentials: {TEST_EMAIL}")
    print("-" * 50)
    
    # Test login flow
    login_result = test_login_flow()
    if not login_result:
        print("\n❌ JWT Authentication Tests FAILED - Login issues")
        return
    
    session, access_token, refresh_token = login_result
    
    # Test protected route access
    if not test_protected_route_access(session):
        print("\n❌ JWT Authentication Tests FAILED - Protected route issues")
        return
    
    # Test token refresh
    if not test_token_refresh(access_token, refresh_token):
        print("\n❌ JWT Authentication Tests FAILED - Token refresh issues")
        return
    
    # Test logout
    if not test_logout(session):
        print("\n❌ JWT Authentication Tests FAILED - Logout issues")
        return
    
    # Test homepage behavior
    if not test_homepage_redirect():
        print("\n❌ JWT Authentication Tests FAILED - Homepage issues")
        return
    
    print("\n" + "=" * 50)
    print("🎉 ALL JWT AUTHENTICATION TESTS PASSED!")
    print("✓ Login with JWT token generation")
    print("✓ Protected route access")
    print("✓ Token refresh functionality")
    print("✓ Logout with cookie clearing")
    print("✓ Homepage redirect behavior")
    print("=" * 50)

if __name__ == "__main__":
    main()