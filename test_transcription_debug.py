#!/usr/bin/env python3
"""
Quick debug test for transcription functionality.
"""
import os
from app.utils.audio_utils import transcribe_audio
from app.config import settings

def create_minimal_audio():
    """Create minimal valid audio data for testing."""
    # Simple WAV file with minimal audio data
    wav_data = (
        b'RIFF'         # ChunkID
        b'\x2c\x00\x00\x00'  # ChunkSize (44 bytes)
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
        b'\x08\x00\x00\x00'  # Subchunk2Size (8 bytes of audio data)
        b'\x00\x00\x00\x00\x00\x00\x00\x00'  # 8 bytes of silence
    )
    return wav_data

def test_transcription():
    """Test the transcription function with minimal audio."""
    print("🔧 Testing transcription function...")
    
    # Check API key
    api_key = settings.OPENAI_API_KEY
    print(f"OpenAI API Key configured: {bool(api_key)}")
    if api_key:
        print(f"API Key length: {len(api_key)} characters")
        print(f"API Key starts with: {api_key[:10]}..." if len(api_key) > 10 else api_key)
    
    # Create test audio
    audio_data = create_minimal_audio()
    print(f"Created test audio: {len(audio_data)} bytes")
    
    # Test transcription
    try:
        result = transcribe_audio(
            audio_data=audio_data,
            filename="test.wav",
            user_language="en",
            audio_duration=1
        )
        
        if result:
            print(f"✅ Transcription successful: '{result}'")
        else:
            print("❌ Transcription returned None")
            
    except Exception as e:
        print(f"❌ Transcription failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_transcription()