"""
Audio processing utilities for Smriti.

This module provides functions for handling audio files and transcription.
"""
import logging
import os
import tempfile
from typing import Dict, Any, Optional

from openai import OpenAI

from app.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client with API key from settings
client = OpenAI(api_key=settings.OPENAI_API_KEY)

def transcribe_audio(audio_data: bytes, filename: str = "audio.webm") -> Optional[str]:
    """
    Transcribe audio data using OpenAI's Whisper model.
    
    Args:
        audio_data: Raw audio data in bytes.
        filename: Name of the temporary file to create (must include extension).
        
    Returns:
        Transcribed text or None if transcription failed.
    """
    logger.info(f"Transcribing audio data of {len(audio_data)} bytes")
    
    temp_filepath = None
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix=os.path.splitext(filename)[1], delete=False) as temp_file:
            temp_filepath = temp_file.name
            # Write the audio data to the temporary file
            temp_file.write(audio_data)
        
        logger.info(f"Temporary audio file created at {temp_filepath}")
        
        # Transcribe the audio file using OpenAI's Whisper model with punctuation prompt
        with open(temp_filepath, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                prompt="Transcribe the following audio with proper punctuation, including periods, commas, and question marks. Format complete sentences properly."
            )
            
        # Get the transcribed text
        transcribed_text = response.text
        logger.info(f"Audio transcription successful. Text length: {len(transcribed_text)}")
        
        return transcribed_text
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}", exc_info=True)
        return None
    finally:
        # Clean up the temporary file if it exists
        if temp_filepath and os.path.exists(temp_filepath):
            try:
                os.unlink(temp_filepath)
                logger.info(f"Temporary file {temp_filepath} removed")
            except Exception as e:
                logger.error(f"Error removing temporary file: {e}")