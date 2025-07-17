"""
Audio processing utilities for Smriti.

This module provides functions for handling audio files and transcription.
"""
import logging
import os
import tempfile
import re
from typing import Dict, Any, Optional

from openai import OpenAI

from app.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client with extended timeout for 5+ minute audio files
client = OpenAI(
    api_key=settings.OPENAI_API_KEY,
    timeout=420.0,  # 7 minutes timeout for OpenAI API calls (5 min audio + processing time)
    max_retries=1   # Single retry to avoid excessive wait times
)

# Language script patterns for validation - OpenAI Whisper supported languages only
SCRIPT_PATTERNS = {
    'ar': r'[\u0600-\u06FF\u0750-\u077F]',  # Arabic script
    'hi': r'[\u0900-\u097F]',              # Devanagari script (Hindi)
    'ur': r'[\u0600-\u06FF\u0750-\u077F]', # Arabic script (Urdu)
    'zh': r'[\u4e00-\u9fff]',              # CJK Unified Ideographs
    'ja': r'[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]', # Hiragana, Katakana, Kanji
    'ko': r'[\uac00-\ud7af\u1100-\u11ff\u3130-\u318f]', # Korean
    'th': r'[\u0e00-\u0e7f]',              # Thai
    'ta': r'[\u0b80-\u0bff]',              # Tamil
    'mr': r'[\u0900-\u097f]',              # Marathi (Devanagari)
    'ne': r'[\u0900-\u097f]',              # Nepali (Devanagari)
    'kn': r'[\u0c80-\u0cff]',              # Kannada
}


def assess_transcription_quality(transcript: str, user_language: Optional[str] = None, audio_duration: Optional[int] = None) -> Dict[str, Any]:
    """
    Assess the quality of a transcription using heuristics.
    
    Args:
        transcript: The transcribed text to assess
        user_language: User's preferred language (ISO 639-1 code)
        audio_duration: Duration of the audio in seconds
        
    Returns:
        Dictionary with quality metrics and overall assessment
    """
    if not transcript or not transcript.strip():
        return {
            'is_good_quality': False,
            'reason': 'empty_transcript',
            'word_count': 0,
            'character_count': 0,
            'script_match': False
        }
    
    transcript = transcript.strip()
    words = transcript.split()
    word_count = len(words)
    character_count = len(transcript)
    
    # Basic quality checks
    if word_count < 3:
        return {
            'is_good_quality': False,
            'reason': 'too_few_words',
            'word_count': word_count,
            'character_count': character_count,
            'script_match': False
        }
    
    if character_count < 10:
        return {
            'is_good_quality': False,
            'reason': 'too_short',
            'word_count': word_count,
            'character_count': character_count,
            'script_match': False
        }
    
    # Check for excessive repetition (same word repeated >3 times)
    word_freq = {}
    for word in words:
        word_freq[word] = word_freq.get(word, 0) + 1
    
    max_repetition = max(word_freq.values()) if word_freq else 0
    if max_repetition > 3 and word_count < 10:
        return {
            'is_good_quality': False,
            'reason': 'excessive_repetition',
            'word_count': word_count,
            'character_count': character_count,
            'script_match': False
        }
    
    # Check script match for non-Latin languages (flexible for multilingual content)
    script_match = True
    if user_language and user_language in SCRIPT_PATTERNS:
        pattern = SCRIPT_PATTERNS[user_language]
        script_chars = len(re.findall(pattern, transcript))
        total_chars = len(re.sub(r'\s+', '', transcript))  # Remove whitespace
        
        if total_chars > 0:
            script_ratio = script_chars / total_chars
            # For Hindi and other code-mixed languages, be more flexible
            # OpenAI Whisper may return English text for Hindi speech if it's clearer
            if user_language == 'hi':  # Hindi language
                # Accept if any Hindi script is present OR if content seems translated
                script_match = script_ratio >= 0.1 or total_chars > 20  # Very lenient for Hindi
            else:
                # For other languages, require 30% script match
                script_match = script_ratio >= 0.3
        else:
            script_match = False
    
    # Audio duration vs transcript length check
    duration_mismatch = False
    if audio_duration and audio_duration > 10:  # Only check for longer audio
        # Rough estimate: 150-200 words per minute for normal speech
        expected_words = (audio_duration / 60) * 100  # Conservative estimate
        if word_count < (expected_words * 0.3):  # Much shorter than expected
            duration_mismatch = True
    
    is_good_quality = script_match and not duration_mismatch
    
    return {
        'is_good_quality': is_good_quality,
        'reason': 'good' if is_good_quality else ('script_mismatch' if not script_match else 'duration_mismatch'),
        'word_count': word_count,
        'character_count': character_count,
        'script_match': script_match,
        'duration_mismatch': duration_mismatch
    }


def choose_better_transcription(result1: Optional[str], result2: Optional[str], user_language: Optional[str] = None, audio_duration: Optional[int] = None) -> Optional[str]:
    """
    Choose the better transcription between two results.
    
    Args:
        result1: First transcription result (with user language)
        result2: Second transcription result (auto-detected)
        user_language: User's preferred language
        audio_duration: Audio duration in seconds
        
    Returns:
        The better transcription or None if both are poor
    """
    if not result1 and not result2:
        return None
    
    if not result1:
        return result2
        
    if not result2:
        return result1
    
    # Assess quality of both transcriptions
    quality1 = assess_transcription_quality(result1, user_language, audio_duration)
    quality2 = assess_transcription_quality(result2, user_language, audio_duration)
    
    # If both are good quality, prefer the one with user's language
    if quality1['is_good_quality'] and quality2['is_good_quality']:
        # For user language transcriptions, prefer them even with script flexibility
        # OpenAI Whisper may return English text for non-English speech if clearer
        logger.info(f"Both transcriptions good quality. User language: {user_language}, Script match: {quality1['script_match']}")
        return result1  # Prefer user's language preference result
    
    # If only one is good quality, return that one
    if quality1['is_good_quality']:
        return result1
    elif quality2['is_good_quality']:
        return result2
    
    # If neither is good quality, return the longer one
    if len(result1.strip()) > len(result2.strip()):
        return result1
    else:
        return result2


def transcribe_audio_with_language(audio_data: bytes, filename: str, language: Optional[str] = None, audio_duration: Optional[int] = None) -> Optional[str]:
    """
    Transcribe audio with optional language specification and automatic fallback.
    
    Args:
        audio_data: Raw audio data in bytes
        filename: Name of the temporary file to create
        language: Optional language code (ISO 639-1)
        audio_duration: Optional audio duration in seconds
        
    Returns:
        Transcribed text or None if transcription failed
    """
    logger.info(f"Transcribing audio data of {len(audio_data)} bytes with language: {language}")
    
    temp_filepath = None
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix=os.path.splitext(filename)[1], delete=False) as temp_file:
            temp_filepath = temp_file.name
            temp_file.write(audio_data)
        
        logger.info(f"Temporary audio file created at {temp_filepath}")
        
        result_with_language = None
        result_auto = None
        
        # First attempt: with user's preferred language
        if language:
            try:
                logger.info(f"Starting language-specific transcription for '{language}'")
                with open(temp_filepath, "rb") as audio_file:
                    response = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language=language,
                        prompt="Transcribe the following audio with proper punctuation, including periods, commas, and question marks. Format complete sentences properly."
                    )
                    result_with_language = response.text
                    logger.info(f"Transcription with language '{language}' successful: {len(result_with_language)} characters")
            except Exception as e:
                logger.error(f"Transcription with language '{language}' failed: {e}")
                result_with_language = None
        
        # Second attempt: auto-detection (no language specified) - only if first attempt failed
        if not result_with_language:
            try:
                logger.info("Starting auto-detection transcription")
                with open(temp_filepath, "rb") as audio_file:
                    response = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        prompt="Transcribe the following audio with proper punctuation, including periods, commas, and question marks. Format complete sentences properly."
                    )
                    result_auto = response.text
                    logger.info(f"Auto-detection transcription successful: {len(result_auto)} characters")
            except Exception as e:
                logger.error(f"Auto-detection transcription failed: {e}")
                result_auto = None
        else:
            logger.info("Skipping auto-detection since language-specific transcription succeeded")
            result_auto = None
        
        # Choose the better result
        final_result = choose_better_transcription(result_with_language, result_auto, language, audio_duration)
        
        if final_result:
            # Log which approach was used with detailed reasoning
            if final_result == result_with_language and language:
                logger.info(f"✓ Selected user language '{language}' transcription: '{final_result[:100]}...'")
            elif result_auto:
                logger.info(f"✓ Selected auto-detection transcription: '{final_result[:100]}...'")
            else:
                logger.info(f"✓ Selected language-specific transcription (no auto-detection attempted): '{final_result[:100]}...'")
            
            return final_result
        else:
            logger.error("Both transcription attempts failed or produced poor quality results")
            return None
            
    except Exception as e:
        logger.error(f"Error in transcription process: {e}", exc_info=True)
        return None
    finally:
        # Clean up the temporary file
        if temp_filepath and os.path.exists(temp_filepath):
            try:
                os.unlink(temp_filepath)
                logger.info(f"Temporary file {temp_filepath} removed")
            except Exception as e:
                logger.error(f"Error removing temporary file: {e}")


def transcribe_audio(audio_data: bytes, filename: str = "audio.webm", user_language: Optional[str] = None, audio_duration: Optional[int] = None) -> Optional[str]:
    """
    Transcribe audio data using OpenAI's Whisper model with automatic language optimization.
    
    This function automatically tries the user's preferred language first, then falls back
    to auto-detection if needed, providing the best transcription quality seamlessly.
    
    Args:
        audio_data: Raw audio data in bytes.
        filename: Name of the temporary file to create (must include extension).
        user_language: User's preferred language (ISO 639-1 code, e.g., 'hi', 'es', 'fr').
        audio_duration: Audio duration in seconds for quality assessment.
        
    Returns:
        Transcribed text or None if transcription failed.
    """
    try:
        # Use the enhanced transcription with language optimization
        result = transcribe_audio_with_language(audio_data, filename, user_language, audio_duration)
        return result
    except Exception as e:
        logger.error(f"Transcription failed: {e}", exc_info=True)
        raise