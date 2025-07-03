"""
Simple script to list available API routes.
"""
import requests
import json

# Base URL for API
BASE_URL = "http://127.0.0.1:8000/api/v1"

# Test some known endpoints
endpoints = [
    "/users/",
    "/sessions/",
    "/nodes/embeddings/batch",
    "/edges/batch",
    "/edges/process_batch",  # Alternative endpoint name
]

print("Testing API endpoints:")
for endpoint in endpoints:
    try:
        # Try a GET request first
        get_response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
        status = get_response.status_code
        print(f"GET {endpoint}: {status}")
    except Exception as e:
        print(f"GET {endpoint}: Error - {e}")
    
    # For POST endpoints, try with empty data
    if endpoint in ["/edges/batch", "/edges/process_batch", "/nodes/embeddings/batch"]:
        try:
            post_response = requests.post(
                f"{BASE_URL}{endpoint}", 
                json={},
                timeout=5
            )
            status = post_response.status_code
            print(f"POST {endpoint}: {status}")
            if status != 405:  # If not Method Not Allowed
                print(f"  Response: {post_response.text[:100]}")
        except Exception as e:
            print(f"POST {endpoint}: Error - {e}")

# Also check for root endpoint documentation
try:
    docs_response = requests.get("http://127.0.0.1:8000/docs", timeout=5)
    if docs_response.status_code == 200:
        print("\nSwagger documentation is available at http://127.0.0.1:8000/docs")
    else:
        print(f"\nSwagger documentation not available: {docs_response.status_code}")
except Exception as e:
    print(f"\nError checking docs endpoint: {e}")