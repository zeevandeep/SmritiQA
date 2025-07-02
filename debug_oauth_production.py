#!/usr/bin/env python3
"""
Debug script to test Google OAuth configuration for production environment.
This will help identify configuration differences between dev and production.
"""

import os
import requests
import json

def test_oauth_config():
    """Test OAuth configuration on published app."""
    
    base_url = "https://smriti-unnati.replit.app"
    
    print("=== Google OAuth Production Debug ===")
    print(f"Testing published app: {base_url}")
    
    # Test 1: Check OAuth stats endpoint
    print("\n1. Checking OAuth stats...")
    try:
        response = requests.get(f"{base_url}/api/v1/auth/google/stats", timeout=10)
        if response.status_code == 200:
            stats = response.json()
            print(f"   ✓ Stats endpoint accessible")
            print(f"   Total users: {stats.get('total_users', 'N/A')}")
            print(f"   Google users: {stats.get('google_oauth_users', 'N/A')}")
        else:
            print(f"   ✗ Stats endpoint error: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Stats endpoint failed: {e}")
    
    # Test 2: Check if OAuth login endpoint is accessible
    print("\n2. Testing OAuth login endpoint...")
    try:
        response = requests.get(f"{base_url}/api/v1/auth/google/login", 
                              allow_redirects=False, timeout=10)
        if response.status_code == 302:
            redirect_url = response.headers.get('Location', '')
            if 'accounts.google.com' in redirect_url:
                print(f"   ✓ OAuth login redirects to Google")
                print(f"   Redirect URL contains: {redirect_url[:100]}...")
                
                # Extract client_id from redirect URL
                if 'client_id=' in redirect_url:
                    client_start = redirect_url.find('client_id=') + 10
                    client_end = redirect_url.find('&', client_start)
                    if client_end == -1:
                        client_end = len(redirect_url)
                    client_id = redirect_url[client_start:client_end]
                    print(f"   Client ID in use: {client_id[:20]}...")
                
                # Extract redirect_uri from redirect URL
                if 'redirect_uri=' in redirect_url:
                    uri_start = redirect_url.find('redirect_uri=') + 13
                    uri_end = redirect_url.find('&', uri_start)
                    if uri_end == -1:
                        uri_end = len(redirect_url)
                    # URL decode the redirect_uri
                    import urllib.parse
                    redirect_uri = urllib.parse.unquote(redirect_url[uri_start:uri_end])
                    print(f"   Redirect URI: {redirect_uri}")
                    
            else:
                print(f"   ✗ OAuth login redirects to: {redirect_url}")
        else:
            print(f"   ✗ OAuth login endpoint error: {response.status_code}")
    except Exception as e:
        print(f"   ✗ OAuth login endpoint failed: {e}")
    
    # Test 3: Check environment differences
    print("\n3. Environment comparison...")
    print("   Development environment:")
    print(f"      REPLIT_DEV_DOMAIN: {os.getenv('REPLIT_DEV_DOMAIN', 'Not set')}")
    print(f"      REPLIT_DOMAINS: {os.getenv('REPLIT_DOMAINS', 'Not set')}")
    print(f"      GOOGLE_OAUTH_CLIENT_ID: {'Set' if os.getenv('GOOGLE_OAUTH_CLIENT_ID') else 'Not set'}")
    
    print("\n=== Recommendations ===")
    print("1. Check Google Cloud Console for authorized redirect URIs")
    print("2. Ensure https://smriti-unnati.replit.app/api/v1/auth/google/callback is whitelisted")
    print("3. Verify the same GOOGLE_OAUTH_CLIENT_ID is used in production")
    print("4. Test with a different Google account")
    print("5. Clear browser cache/cookies and try again")

if __name__ == "__main__":
    test_oauth_config()