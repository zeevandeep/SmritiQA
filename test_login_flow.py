#!/usr/bin/env python3
"""
Test the actual login flow with real credentials to see debug output.
"""

import requests

def test_login_flow():
    """Test the login flow and observe debug output."""
    print("Testing login flow...")
    
    session = requests.Session()
    
    # First, check if we can access the login page
    print("1. Accessing login page...")
    response = session.get("http://localhost:5000/login")
    print(f"   Login page status: {response.status_code}")
    
    # Try to login with existing user
    print("2. Attempting login...")
    login_data = {
        'email': 'jindal.siddharth1@gmail.com',
        'password': 'testpass'  # You'll need to know the actual password
    }
    
    response = session.post("http://localhost:5000/login", data=login_data, allow_redirects=False)
    print(f"   Login response status: {response.status_code}")
    print(f"   Response headers: {dict(response.headers)}")
    
    if response.status_code == 303:
        print("   ✓ Login successful - got redirect")
        print(f"   Redirect location: {response.headers.get('location')}")
        
        # Check cookies
        cookies = session.cookies
        print(f"   Cookies set: {list(cookies.keys())}")
        
        # Try to access protected route
        print("3. Testing protected route access...")
        response = session.get("http://localhost:5000/journal", allow_redirects=False)
        print(f"   Journal access status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✓ Protected route accessible")
        else:
            print(f"   ✗ Protected route failed: {response.status_code}")
    else:
        print("   ✗ Login failed")
        print(f"   Response text: {response.text[:200]}...")

if __name__ == "__main__":
    test_login_flow()