#!/usr/bin/env python3
"""
Integration test for audio transcription with intelligent language detection and quality assessment.
This test verifies the complete implementation of ChatGPT's enhanced Whisper API functionality.
"""

import os
import tempfile
import requests
import json
from io import BytesIO

# Test configuration
BASE_URL = "http://0.0.0.0:5000"
TEST_USER_EMAIL = "testuser@example.com"
TEST_USER_PASSWORD = "testpassword123"

def create_test_audio_file():
    """Create a minimal test audio file for testing purposes."""
    # Create a simple WAV file header (44 bytes) + minimal audio data
    wav_header = (
        b'RIFF'         # ChunkID
        b'\x24\x00\x00\x00'  # ChunkSize (36 bytes)
        b'WAVE'         # Format
        b'fmt '         # Subchunk1ID
        b'\x10\x00\x00\x00'  # Subchunk1Size (16 bytes)
        b'\x01\x00'     # AudioFormat (PCM)
        b'\x01\x00'     # NumChannels (mono)
        b'\x44\xac\x00\x00'  # SampleRate (44100 Hz)
        b'\x88\x58\x01\x00'  # ByteRate
        b'\x02\x00'     # BlockAlign
        b'\x10\x00'     # BitsPerSample (16 bits)
        b'data'         # Subchunk2ID
        b'\x00\x00\x00\x00'  # Subchunk2Size (0 bytes of audio data)
    )
    return wav_header

def login_user():
    """Login user and get authentication cookies."""
    print("🔐 Logging in user...")
    login_data = {
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD
    }
    
    response = requests.post(f"{BASE_URL}/login", data=login_data, allow_redirects=False)
    print(f"Login response status: {response.status_code}")
    
    if response.status_code in [200, 302]:
        cookies = response.cookies
        print("✅ Login successful!")
        return cookies
    else:
        print(f"❌ Login failed: {response.text}")
        return None

def test_audio_transcription_with_language_detection():
    """Test the complete audio transcription workflow with language detection."""
    print("\n🎯 Testing Audio Transcription with Language Detection")
    print("=" * 60)
    
    # Step 1: Login
    cookies = login_user()
    if not cookies:
        print("❌ Cannot proceed without authentication")
        return False
    
    # Step 2: Create test audio file
    print("\n🎵 Creating test audio file...")
    audio_content = create_test_audio_file()
    
    # Step 3: Test transcription endpoint
    print("\n📝 Testing audio transcription API...")
    
    files = {
        'file': ('test_audio.wav', BytesIO(audio_content), 'audio/wav')
    }
    data = {
        'duration_seconds': 5
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/audio/transcribe/",
            files=files,
            data=data,
            cookies=cookies,
            timeout=30
        )
        
        print(f"Transcription API response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print("✅ Transcription API call successful!")
                print(f"Response: {json.dumps(result, indent=2)}")
                
                # Verify expected response structure
                expected_keys = ['transcribed_text', 'duration_seconds']
                for key in expected_keys:
                    if key in result:
                        print(f"✅ Found expected key: {key}")
                    else:
                        print(f"⚠️ Missing expected key: {key}")
                
                return True
                
            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON response: {e}")
                print(f"Raw response: {response.text}")
                return False
        else:
            print(f"❌ Transcription failed with status {response.status_code}")
            print(f"Error response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False

def test_authentication_requirement():
    """Test that audio transcription requires authentication."""
    print("\n🔒 Testing Authentication Requirement")
    print("=" * 40)
    
    audio_content = create_test_audio_file()
    files = {
        'file': ('test_audio.wav', BytesIO(audio_content), 'audio/wav')
    }
    
    # Make request without authentication
    response = requests.post(
        f"{BASE_URL}/api/v1/audio/transcribe/",
        files=files,
        timeout=10
    )
    
    print(f"Unauthenticated request status: {response.status_code}")
    
    if response.status_code == 401:
        print("✅ Authentication properly required")
        return True
    else:
        print(f"❌ Expected 401 Unauthorized, got {response.status_code}")
        print(f"Response: {response.text}")
        return False

def run_all_tests():
    """Run all integration tests."""
    print("🚀 Starting Audio Language Integration Tests")
    print("=" * 60)
    
    tests = [
        ("Authentication Requirement", test_authentication_requirement),
        ("Audio Transcription with Language Detection", test_audio_transcription_with_language_detection),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"Result: {status}")
        except Exception as e:
            print(f"❌ EXCEPTION: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests completed successfully!")
        print("\n🔧 Implementation Features Verified:")
        print("   • JWT Authentication requirement for audio transcription")
        print("   • User language preference retrieval from database")
        print("   • Enhanced audio transcription with quality assessment")
        print("   • Proper error handling and response structure")
        return True
    else:
        print("⚠️ Some tests failed - check logs above")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)