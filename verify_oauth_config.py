#!/usr/bin/env python3
"""
Verify the exact OAuth configuration being used by the published app.
"""

import requests
import urllib.parse

def verify_oauth_config():
    """Verify OAuth configuration details."""
    
    print("=== OAuth Configuration Verification ===")
    
    # Get the authorization URL from published app
    try:
        response = requests.get(
            "https://smriti-unnati.replit.app/api/v1/auth/google/login",
            allow_redirects=False,
            timeout=10
        )
        
        if response.status_code == 302:
            auth_url = response.headers.get('Location', '')
            print(f"Authorization URL: {auth_url}")
            
            # Parse the URL to extract parameters
            parsed = urllib.parse.urlparse(auth_url)
            params = urllib.parse.parse_qs(parsed.query)
            
            print(f"\n=== Extracted Parameters ===")
            print(f"Client ID: {params.get('client_id', ['N/A'])[0]}")
            
            redirect_uri = params.get('redirect_uri', ['N/A'])[0]
            print(f"Redirect URI: {redirect_uri}")
            
            # Check for exact match issues
            expected_uri = "https://smriti-unnati.replit.app/api/v1/auth/google/callback"
            
            print(f"\n=== URI Comparison ===")
            print(f"Expected: '{expected_uri}'")
            print(f"Actual:   '{redirect_uri}'")
            print(f"Match: {redirect_uri == expected_uri}")
            
            if redirect_uri != expected_uri:
                print(f"\n=== Differences ===")
                print(f"Length - Expected: {len(expected_uri)}, Actual: {len(redirect_uri)}")
                
                # Character by character comparison
                for i, (e, a) in enumerate(zip(expected_uri, redirect_uri)):
                    if e != a:
                        print(f"Difference at position {i}: expected '{e}' but got '{a}'")
                        break
            
            print(f"\n=== Google Cloud Console Instructions ===")
            print(f"1. Go to: https://console.cloud.google.com/apis/credentials")
            print(f"2. Find Client ID: {params.get('client_id', ['N/A'])[0]}")
            print(f"3. Ensure this EXACT URI is listed:")
            print(f"   {redirect_uri}")
            print(f"4. Check for:")
            print(f"   - No trailing spaces")
            print(f"   - No extra characters")
            print(f"   - Exact case match")
            print(f"   - HTTPS (not HTTP)")
            
        else:
            print(f"Unexpected response: {response.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_oauth_config()