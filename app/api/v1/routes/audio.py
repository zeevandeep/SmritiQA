"""
Audio processing routes for API v1.
"""
from fastapi import APIRouter, File, Form, HTTPException, status, UploadFile
from fastapi.responses import JSONResponse

from app.utils.audio_utils import transcribe_audio

router = APIRouter()


@router.post("/transcribe/", status_code=status.HTTP_200_OK)
async def transcribe_audio_file(file: UploadFile = File(...), duration_seconds: int = Form(None)):
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
    
    # Read the file content
    file_content = await file.read()
    
    # Transcribe the audio
    filename = file.filename if file.filename else "audio.webm"
    transcribed_text = transcribe_audio(file_content, filename=filename)
    
    if transcribed_text is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to transcribe audio"
        )
    
    logger.info(f"Transcription successful, returning text with duration: {duration_seconds}")
    return {
        "transcript": transcribed_text,
        "duration_seconds": duration_seconds
    }