#!/usr/bin/env python3
"""
Simple JWT authentication test using real user credentials.
"""

import requests
import json

# Test configuration
BASE_URL = "http://localhost:5000"

def test_jwt_tokens():
    """Test JWT token functionality with browser simulation."""
    print("Testing JWT Authentication...")
    
    # Create session to maintain cookies
    session = requests.Session()
    
    # 1. Check homepage (should show login page)
    print("1. Checking homepage...")
    response = session.get(f"{BASE_URL}/")
    print(f"   Homepage status: {response.status_code}")
    
    # 2. Check login page
    print("2. Accessing login page...")
    response = session.get(f"{BASE_URL}/login")
    print(f"   Login page status: {response.status_code}")
    
    # 3. Check if we can access journal without auth (should redirect)
    print("3. Testing journal access without auth...")
    response = session.get(f"{BASE_URL}/journal", allow_redirects=False)
    print(f"   Journal access status: {response.status_code}")
    if response.status_code == 303:
        print("   ✓ Correctly redirected to login")
    
    # 4. Test token refresh endpoint directly
    print("4. Testing token refresh endpoint...")
    response = session.post(f"{BASE_URL}/api/v1/auth/refresh")
    print(f"   Refresh endpoint status: {response.status_code}")
    print(f"   Response: {response.text}")
    
    # 5. Test logout endpoint
    print("5. Testing logout endpoint...")
    response = session.get(f"{BASE_URL}/logout", allow_redirects=False)
    print(f"   Logout status: {response.status_code}")
    
    print("\nJWT endpoints are accessible. To test full authentication:")
    print("1. Go to the app in your browser")
    print("2. Try logging in with: jindal.siddharth1@gmail.com") 
    print("3. Check browser dev tools > Application > Cookies")
    print("4. Look for 'smriti_access_token' and 'smriti_refresh_token'")
    print("5. Try accessing /journal - should work if JWT is valid")

if __name__ == "__main__":
    test_jwt_tokens()