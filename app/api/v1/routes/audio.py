"""
Audio processing routes for API v1.
"""
from fastapi import APIRouter, File, Form, HTTPException, status, UploadFile, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from uuid import UUID

from app.utils.audio_utils import transcribe_audio
from app.db.database import get_db
from app.repositories import user_repository
from app.utils.api_auth import get_current_user_from_jwt

router = APIRouter()


@router.post("/transcribe/", status_code=status.HTTP_200_OK)
async def transcribe_audio_file(
    file: UploadFile = File(...), 
    duration_seconds: int = Form(None),
    current_user_id: str = Depends(get_current_user_from_jwt),
    db: Session = Depends(get_db)
):
    """
    Transcribe an audio file using OpenAI's Whisper model.
    
    Args:
        file: The audio file to transcribe.
        duration_seconds: Optional duration of the recording in seconds.
        
    Returns:
        JSONResponse: The transcribed text and duration.
        
    Raises:
        HTTPException: If the file is not an audio file or transcription fails.
    """
    # Log received parameters
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Received transcription request with duration: {duration_seconds}")
    
    # Check if the file is an audio file
    if file.content_type and not file.content_type.startswith("audio/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an audio file"
        )
    
    # Get user's language preference from database
    user_id_uuid = UUID(current_user_id)
    user_language = user_repository.get_user_language(db, user_id_uuid)
    logger.info(f"User language preference: {user_language}")
    
    # Read the file content
    file_content = await file.read()
    
    # Transcribe the audio with user's language preference
    filename = file.filename if file.filename else "audio.webm"
    logger.info(f"Starting transcription with file: {filename}, size: {len(file_content)} bytes")
    
    try:
        print(f"API DEBUG: About to call transcribe_audio with {len(file_content)} bytes, language={user_language}")
        transcribed_text = transcribe_audio(
            file_content, 
            filename=filename, 
            user_language=user_language,
            audio_duration=duration_seconds
        )
        print(f"API DEBUG: transcribe_audio returned: {transcribed_text is not None}")
        
        if transcribed_text is None:
            logger.error("Transcription returned None - OpenAI API might have failed")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to transcribe audio - please try again"
            )
        
        logger.info(f"Transcription successful: '{transcribed_text[:100]}...' (duration: {duration_seconds}s)")
        return {
            "transcribed_text": transcribed_text,  # Fixed: frontend expects this field name
            "duration_seconds": duration_seconds
        }
        
    except Exception as e:
        logger.error(f"Transcription error: {e}", exc_info=True)
        print(f"API TRANSCRIPTION ERROR: {e}")  # Force console output
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transcription failed: {str(e)}"
        )