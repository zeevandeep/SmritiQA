"""
Test direct connection to FastAPI server.
"""
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Connect directly to the uvicorn server
BASE_URL = "http://127.0.0.1:8000"

try:
    print("Testing direct connection to FastAPI server...")
    response = requests.get(f"{BASE_URL}/")
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text}")
except Exception as e:
    print(f"Error connecting to FastAPI server: {e}")