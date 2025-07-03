"""
Test script for Phase 1 functionality of the Smriti API.

This script tests the end-to-end flow of Phase 1:
1. Create a user
2. Create a user profile
3. Create a session
4. Update a session with transcript
"""
import requests
import json
from uuid import UUID

# Base URL for the API
BASE_URL = "http://localhost:5000/api/v1"

def test_phase1():
    """Test Phase 1 functionality."""
    print("=== Testing Phase 1 Functionality ===")
    
    # 1. Create a user
    print("\n1. Creating a user...")
    user_data = {
        "email": "test@example.com"
    }
    response = requests.post(f"{BASE_URL}/users/", json=user_data)
    
    if response.status_code == 201:
        user = response.json()
        user_id = user["id"]
        print(f"User created with ID: {user_id}")
    else:
        print(f"Failed to create user: {response.status_code} {response.text}")
        # Try to get an existing user
        response = requests.get(f"{BASE_URL}/users/")
        if response.status_code == 200 and response.json():
            user = response.json()[0]
            user_id = user["id"]
            print(f"Using existing user with ID: {user_id}")
        else:
            print("Could not create or find a user.")
            return
    
    # 2. Create a user profile
    print("\n2. Creating a user profile...")
    profile_data = {
        "display_name": "Test User",
        "language": "en",
        "gender": "prefer not to say"
    }
    response = requests.post(f"{BASE_URL}/users/{user_id}/profile", json=profile_data)
    
    if response.status_code == 201:
        profile = response.json()
        print(f"Profile created for user: {profile['display_name']}")
    elif response.status_code == 400 and "Profile already exists" in response.text:
        # Profile already exists, try to get it
        response = requests.get(f"{BASE_URL}/users/{user_id}/profile")
        if response.status_code == 200:
            profile = response.json()
            print(f"Using existing profile for user: {profile['display_name']}")
        else:
            print(f"Failed to retrieve existing profile: {response.status_code} {response.text}")
    else:
        print(f"Failed to create profile: {response.status_code} {response.text}")
    
    # 3. Create a session
    print("\n3. Creating a session...")
    session_data = {
        "user_id": user_id,
        "duration_seconds": 300,  # 5 minutes session
        "raw_transcript": None  # We'll update this later
    }
    response = requests.post(f"{BASE_URL}/sessions/", json=session_data)
    
    if response.status_code == 201:
        session = response.json()
        session_id = session["id"]
        print(f"Session created with ID: {session_id}")
    else:
        print(f"Failed to create session: {response.status_code} {response.text}")
        return
    
    # 4. Update the session with a transcript
    print("\n4. Updating session with transcript...")
    transcript = "Today I felt happy about my progress at work. I completed a project that's been difficult, and my boss was pleased with the results. This gives me confidence that I'm on the right track with my career."
    
    # Create a JSON payload with the transcript
    transcript_data = {"transcript": transcript}
    response = requests.put(
        f"{BASE_URL}/sessions/{session_id}/transcript",
        json=transcript_data
    )
    
    if response.status_code == 200:
        updated_session = response.json()
        print(f"Session updated with transcript. Length: {len(updated_session['raw_transcript'])}")
    else:
        print(f"Failed to update session: {response.status_code} {response.text}")
    
    # 5. Mark the session as processed
    print("\n5. Marking session as processed...")
    response = requests.put(f"{BASE_URL}/sessions/{session_id}/process")
    
    if response.status_code == 200:
        processed_session = response.json()
        print(f"Session marked as processed: {processed_session['is_processed']}")
    else:
        print(f"Failed to mark session as processed: {response.status_code} {response.text}")
    
    print("\n=== Phase 1 Test Complete ===")

if __name__ == "__main__":
    test_phase1()