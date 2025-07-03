"""
Test script for Phase 2 functionality of the Smriti API.

This script tests the end-to-end flow of Phase 2:
1. Create a user (or use existing)
2. Create a session with transcript
3. Process the session to extract nodes
4. Verify that nodes were created
"""
import json
import requests
import uuid
import time
import logging
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Connect directly to FastAPI server
BASE_URL = "http://127.0.0.1:8000/api/v1"

# Add session with retry capability
http_session = requests.Session()
http_session.mount('http://', requests.adapters.HTTPAdapter(max_retries=3))

def test_phase2():
    """Test Phase 2 functionality."""
    print("=== Testing Phase 2 Functionality ===\n")
    
    # 1. Create or get an existing user
    print("1. Creating a user...")
    
    # Try up to 3 times with delays
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            logging.debug(f"Attempt {attempt+1}/{max_attempts} to create user")
            response = http_session.post(
                f"{BASE_URL}/users/",
                json={"email": "phase2@example.com"},
                timeout=10
            )
            logging.debug(f"Response status: {response.status_code}")
            break
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed: {e}")
            if attempt < max_attempts - 1:
                wait_time = 2 ** attempt  # exponential backoff
                logging.debug(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                print(f"Failed after {max_attempts} attempts: {e}")
                return
    
    if response.status_code == 201:
        user = response.json()
        user_id = user["id"]
        print(f"User created with ID: {user_id}")
    elif response.status_code == 400 and ("already exists" in response.text or "already registered" in response.text):
        # User already exists, get user by email
        try:
            response = http_session.get(f"{BASE_URL}/users/", timeout=10)
            if response.status_code == 200:
                users = response.json()
                user = next((u for u in users if u["email"] == "phase2@example.com"), None)
                if user:
                    user_id = user["id"]
                    print(f"Using existing user with ID: {user_id}")
                else:
                    print(f"Could not find existing user.")
                    return
            else:
                print(f"Failed to get users: {response.status_code} {response.text}")
                return
        except requests.exceptions.RequestException as e:
            print(f"Failed to get users: {e}")
            return
    else:
        print(f"Failed to create user: {response.status_code} {response.text}")
        return
    
    # 2. Create a session with transcript
    print("\n2. Creating a session with transcript...")
    transcript = """
    Today was a rollercoaster. I started the day feeling confident about my career path, 
    but by lunch I was questioning if this is really what I want to do with my life.
    When I think about my family, I feel guilty that I don't call my parents enough.
    My relationship with my partner is going well, but sometimes I feel like I'm not 
    good enough for them. I worry they'll eventually see my flaws and leave.
    Money has been tight lately, and I'm anxious about my financial future.
    I've been thinking about my values and what truly matters to me.
    Sometimes I wonder if I'm making any real difference in the world.
    """
    
    # Create the session
    try:
        response = http_session.post(
            f"{BASE_URL}/sessions/",
            json={"user_id": user_id, "duration_seconds": 300},
            timeout=10
        )
    except requests.exceptions.RequestException as e:
        print(f"Failed to create session: {e}")
        return
    
    if response.status_code == 201:
        session = response.json()
        session_id = session["id"]
        print(f"Session created with ID: {session_id}")
    else:
        print(f"Failed to create session: {response.status_code} {response.text}")
        return
    
    # Update the session with transcript
    transcript_data = {"transcript": transcript}
    try:
        response = http_session.put(
            f"{BASE_URL}/sessions/{session_id}/transcript",
            json=transcript_data,
            timeout=10
        )
    except requests.exceptions.RequestException as e:
        print(f"Failed to update session transcript: {e}")
        return
    
    if response.status_code == 200:
        updated_session = response.json()
        print(f"Session updated with transcript. Length: {len(updated_session['raw_transcript'])}")
    else:
        print(f"Failed to update session transcript: {response.status_code} {response.text}")
        return
    
    # 3. Process the session to extract nodes
    print("\n3. Processing session to extract nodes...")
    try:
        # This is likely the longest operation as it uses OpenAI to process the text
        response = http_session.post(
            f"{BASE_URL}/nodes/session/{session_id}/process",
            timeout=60  # Longer timeout for this operation
        )
    except requests.exceptions.RequestException as e:
        print(f"Failed to process nodes: {e}")
        return
    
    if response.status_code == 200:
        nodes = response.json()
        print(f"Successfully processed transcript. Extracted {len(nodes)} nodes:")
        
        # Print a summary of each node
        for i, node in enumerate(nodes, 1):
            print(f"\nNode {i}:")
            print(f"  Text: {node['text'][:50]}..." if len(node['text']) > 50 else f"  Text: {node['text']}")
            print(f"  Emotion: {node['emotion']}")
            print(f"  Theme: {node['theme']}")
            print(f"  Cognition Type: {node['cognition_type']}")
    else:
        print(f"Failed to process transcript: {response.status_code} {response.text}")
        return
    
    # 4. Verify that nodes were created by getting them directly
    print("\n4. Verifying nodes were created in the database...")
    try:
        response = http_session.get(
            f"{BASE_URL}/nodes/session/{session_id}",
            timeout=10
        )
    except requests.exceptions.RequestException as e:
        print(f"Failed to verify nodes: {e}")
        return
    
    if response.status_code == 200:
        db_nodes = response.json()
        print(f"Retrieved {len(db_nodes)} nodes from the database.")
        
        # Verify these are the same nodes we got from processing
        if len(db_nodes) == len(nodes):
            print("Verified: Node count matches.")
        else:
            print(f"Warning: Node count mismatch. API returned {len(nodes)}, database has {len(db_nodes)}.")
    else:
        print(f"Failed to get nodes: {response.status_code} {response.text}")
    
    print("\n=== Phase 2 Test Complete ===")

if __name__ == "__main__":
    test_phase2()