"""
Session repository for database operations related to user sessions.
"""
import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session as DbSession

from app.models.models import Session, MigrationError
from app.schemas.schemas import SessionCreate
from app.utils.encryption import encrypt_data, decrypt_data, EncryptionError

logger = logging.getLogger(__name__)


def get_session(db: DbSession, session_id: UUID) -> Optional[Session]:
    """
    Get a session by ID with automatic decryption.
    
    Args:
        db: Database session.
        session_id: ID of the session to retrieve.
        
    Returns:
        Session object if found, None otherwise.
    """
    db_session = db.query(Session).filter(Session.id == session_id).first()
    
    if db_session and db_session.is_encrypted and db_session.raw_transcript:
        try:
            user_id = str(db_session.user_id)
            # CRITICAL FIX: Create a copy to avoid overwriting database
            # DO NOT modify db_session.raw_transcript directly as it will save back to database
            decrypted_text = decrypt_data(db_session.raw_transcript, user_id)
            
            # Create a completely new Session object with decrypted data (not a copy)
            # This ensures no reference to the original encrypted database object
            decrypted_session = Session(
                id=db_session.id,
                user_id=db_session.user_id,
                raw_transcript=decrypted_text,  # Use decrypted text
                duration_seconds=db_session.duration_seconds,
                created_at=db_session.created_at,
                updated_at=db_session.updated_at,
                is_encrypted=db_session.is_encrypted,
                is_processed=db_session.is_processed
            )
            
            # This object is not attached to SQLAlchemy session, so no risk of accidental saves
            return decrypted_session
            
        except EncryptionError as e:
            logger.error(f"Failed to decrypt session {session_id} for user {user_id}: {e}")
            _log_migration_error(db, db_session.user_id, session_id, "decryption_failed", str(e))
            # Return None to indicate the session is corrupted
            return None
    
    return db_session


def get_user_sessions(db: DbSession, user_id: UUID, skip: int = 0, limit: int = 100) -> List[Session]:
    """
    Get sessions for a user with automatic decryption.
    
    Args:
        db: Database session.
        user_id: ID of the user.
        skip: Number of sessions to skip.
        limit: Maximum number of sessions to return.
        
    Returns:
        List of Session objects.
    """
    sessions = db.query(Session)\
        .filter(Session.user_id == user_id)\
        .order_by(Session.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    # Decrypt encrypted sessions with detached copies to prevent database overwrites
    decrypted_sessions = []
    for session in sessions:
        if session.is_encrypted and session.raw_transcript:
            try:
                # CRITICAL FIX: Create detached copy to prevent overwriting database
                # DO NOT modify session.raw_transcript directly as it will save back to database
                decrypted_text = decrypt_data(session.raw_transcript, str(user_id))
                
                # Create a completely new Session object with decrypted data (not a copy)
                # This ensures no reference to the original encrypted database object
                decrypted_session = Session(
                    id=session.id,
                    user_id=session.user_id,
                    raw_transcript=decrypted_text,  # Use decrypted text
                    duration_seconds=session.duration_seconds,
                    created_at=session.created_at,
                    updated_at=session.updated_at,
                    is_encrypted=session.is_encrypted,
                    is_processed=session.is_processed
                )
                
                # This object is not attached to SQLAlchemy session, so no risk of accidental saves
                decrypted_sessions.append(decrypted_session)
            except EncryptionError as e:
                logger.error(f"Failed to decrypt session {session.id} for user {user_id}: {e}")
                _log_migration_error(db, user_id, session.id, "decryption_failed", str(e))
                # Skip corrupted sessions
                continue
        else:
            decrypted_sessions.append(session)
    
    return decrypted_sessions


def create_session(db: DbSession, session: SessionCreate) -> Session:
    """
    Create a new session with encryption support.
    
    Args:
        db: Database session.
        session: Session data.
        
    Returns:
        Created Session object.
    """
    logger.info(f"[SESSION DEBUG] create_session called")
    logger.info(f"[SESSION DEBUG] session user_id: {session.user_id}")
    logger.info(f"[SESSION DEBUG] session raw_transcript length: {len(session.raw_transcript or '')}")
    
    # Extract values directly from session object (don't use model_dump to avoid reintroducing plain text)
    user_id = session.user_id
    duration_seconds = session.duration_seconds
    original_transcript = session.raw_transcript
    
    # ChatGPT's hardcoded test to detect overwrite patterns
    if original_transcript == "test-overwrite-detect":
        logger.info(f"[OVERWRITE TEST] Detected test phrase, creating hardcoded entry")
        test_session = Session(
            user_id=user_id,
            raw_transcript="THIS_SHOULD_BE_IN_DB",
            duration_seconds=duration_seconds,
            is_encrypted=False,
            is_processed=False
        )
        db.add(test_session)
        db.commit()
        logger.info(f"[OVERWRITE TEST] Test session created with ID: {test_session.id}")
        return test_session
    
    # ChatGPT's poison value test to detect post-creation overwrites
    if original_transcript == "poison-test":
        logger.info(f"[POISON TEST] Creating encrypted session, then poisoning it")
        # Create with encrypted data
        encrypted_transcript = encrypt_data("Original encrypted content", str(user_id))
        poison_session = Session(
            user_id=user_id,
            raw_transcript=encrypted_transcript,
            duration_seconds=duration_seconds,
            is_encrypted=True,
            is_processed=False
        )
        db.add(poison_session)
        db.commit()
        logger.info(f"[POISON TEST] Session created with encrypted data")
        
        # Poison it post-commit
        poison_session.raw_transcript = "POISON_OVERWRITE_SHOULD_NOT_HAPPEN"
        db.commit()
        logger.info(f"[POISON TEST] Session poisoned with plain text")
        return poison_session
    
    # Encrypt raw_transcript if it exists
    if original_transcript and user_id:
        try:
            user_id_str = str(user_id)
            
            logger.info(f"[ENCRYPTION DEBUG] Starting encryption for user {user_id_str}")
            logger.info(f"[ENCRYPTION DEBUG] Original transcript length: {len(original_transcript)}")
            logger.info(f"[ENCRYPTION DEBUG] Original transcript: {original_transcript[:50]}...")
            
            # Encrypt the transcript
            encrypted_transcript = encrypt_data(original_transcript, user_id_str)
            
            # Add SHA256 fingerprint to track data integrity
            import hashlib
            hash_original = hashlib.sha256(original_transcript.encode()).hexdigest()
            hash_encrypted = hashlib.sha256(encrypted_transcript.encode()).hexdigest()
            
            logger.info(f"[ENCRYPTION DEBUG] Encryption successful, length: {len(encrypted_transcript)}")
            logger.info(f"[ENCRYPTION DEBUG] Encrypted transcript: {encrypted_transcript[:50]}...")
            logger.info(f"[SESSION FINGERPRINT] Original hash: {hash_original}")
            logger.info(f"[SESSION FINGERPRINT] Encrypted hash: {hash_encrypted}")
            
            # Create Session object directly with encrypted data - NO model_dump() usage
            db_session = Session(
                user_id=user_id,
                raw_transcript=encrypted_transcript,  # Use encrypted data directly
                duration_seconds=duration_seconds,
                is_encrypted=True,
                is_processed=False
            )
            
            logger.info(f"Session transcript encrypted for user {user_id_str}")
            
        except Exception as e:  # Catch all exceptions, not just EncryptionError
            logger.error(f"[ENCRYPTION DEBUG] Exception during encryption: {type(e).__name__}: {e}")
            import traceback
            logger.error(f"[ENCRYPTION DEBUG] Traceback: {traceback.format_exc()}")
            
            # Create Session object with plain text if encryption fails
            db_session = Session(
                user_id=user_id,
                raw_transcript=original_transcript,
                duration_seconds=duration_seconds,
                is_encrypted=False,
                is_processed=False
            )
            
            # Log the error to migration_errors table
            _log_migration_error(db, user_id, None, "encryption_failed", str(e))
    else:
        # Create Session object with plain text if no transcript
        db_session = Session(
            user_id=user_id,
            raw_transcript=original_transcript,
            duration_seconds=duration_seconds,
            is_encrypted=False,
            is_processed=False
        )
    
    logger.info(f"[SESSION CREATE] Final session object raw_transcript length: {len(db_session.raw_transcript or '')}")
    logger.info(f"[SESSION CREATE] Final session object is_encrypted: {db_session.is_encrypted}")
    logger.info(f"[SESSION CREATE] Final session object raw_transcript: {(db_session.raw_transcript or '')[:50]}...")
    
    db.add(db_session)
    logger.info(f"[SESSION CREATE] After db.add(), raw_transcript length: {len(db_session.raw_transcript or '')}")
    
    # Force flush to database before commit to see if there's an issue
    db.flush()
    logger.info(f"[SESSION CREATE] After db.flush(), raw_transcript length: {len(db_session.raw_transcript or '')}")
    
    db.commit()
    logger.info(f"[SESSION CREATE] After db.commit(), raw_transcript length: {len(db_session.raw_transcript or '')}")
    
    # CRITICAL: Check what's actually in the database immediately after commit
    from sqlalchemy import text
    result = db.execute(text("SELECT LENGTH(raw_transcript), is_encrypted, LEFT(raw_transcript, 50), raw_transcript FROM sessions WHERE id = :session_id"), 
                       {"session_id": str(db_session.id)}).fetchone()
    if result:
        logger.warning(f"[DATABASE REALITY] length: {result[0]}, is_encrypted: {result[1]}")
        logger.warning(f"[DATABASE REALITY] sample: {result[2]}")
        
        # Calculate hash of what's actually in database
        import hashlib
        hash_db = hashlib.sha256(result[3].encode()).hexdigest()
        logger.warning(f"[DATABASE HASH] {hash_db}")
        
        # Check against what we intended (encrypted)
        intended_hash = hashlib.sha256((db_session.raw_transcript or '').encode()).hexdigest()
        logger.warning(f"[INTENDED HASH] {intended_hash}")
        
        # Check against original plain text  
        original_hash = hashlib.sha256(original_transcript.encode()).hexdigest()
        logger.warning(f"[ORIGINAL HASH] {original_hash}")
        
        if hash_db == intended_hash:
            logger.warning(f"[HASH RESULT] ✓ ENCRYPTED DATA in database")
        elif hash_db == original_hash:
            logger.error(f"[HASH RESULT] ✗ PLAIN TEXT in database - ENCRYPTION BYPASSED!")
        else:
            logger.error(f"[HASH RESULT] ✗ UNKNOWN DATA in database")
    
    # ChatGPT's critical fix: Check ACTUAL database state BEFORE expunge
    db.refresh(db_session)
    db_raw = db_session.raw_transcript or ''
    logger.warning(f"[ACTUAL DB] Post-commit value length: {len(db_raw)}")
    logger.warning(f"[ACTUAL DB] Post-commit value sample: {db_raw[:50]}")
    
    import hashlib
    actual_hash = hashlib.sha256(db_raw.encode()).hexdigest()
    logger.warning(f"[ACTUAL DB] Post-commit HASH: {actual_hash}")
    
    # Compare with what we intended to save
    if 'encrypted_transcript' in locals():
        intended_hash = hashlib.sha256(encrypted_transcript.encode()).hexdigest()
        logger.warning(f"[INTENDED] Hash: {intended_hash}")
        if actual_hash == intended_hash:
            logger.warning(f"[RESULT] ✓ Database has ENCRYPTED data")
        else:
            logger.error(f"[RESULT] ✗ Database was OVERWRITTEN with different data!")
    
    # ChatGPT's fix: REMOVE db.expunge() completely - it's not needed
    # db.expunge(db_session)  # REMOVED - was causing verification issues
    
    return db_session


def update_session_transcript(db: DbSession, session_id: UUID, transcript: str) -> Optional[Session]:
    """
    Update a session's transcript.
    
    Args:
        db: Database session.
        session_id: ID of the session.
        transcript: Transcript text.
        
    Returns:
        Updated Session object if found, None otherwise.
    """
    db_session = get_session(db, session_id)
    if db_session is None:
        return None
    
    db_session.raw_transcript = transcript
    db.commit()
    db.refresh(db_session)
    return db_session


def mark_session_processed(db: DbSession, session_id: UUID) -> Optional[Session]:
    """
    Mark a session as processed.
    
    Args:
        db: Database session.
        session_id: ID of the session.
        
    Returns:
        Updated Session object if found, None otherwise.
    """
    db_session = get_session(db, session_id)
    if db_session is None:
        return None
    
    db_session.is_processed = True
    db.commit()
    db.refresh(db_session)
    return db_session


def _log_migration_error(db: DbSession, user_id: UUID, session_id: UUID, error_type: str, error_message: str):
    """
    Log a migration error to the migration_errors table.
    
    Args:
        db: Database session.
        user_id: User ID associated with the error.
        session_id: Session ID associated with the error (can be None).
        error_type: Type of error (e.g., 'encryption_failed', 'decryption_failed').
        error_message: Detailed error message.
    """
    try:
        migration_error = MigrationError(
            user_id=user_id,
            session_id=session_id,
            error_type=error_type,
            error_message=error_message
        )
        db.add(migration_error)
        db.commit()
        logger.info(f"Migration error logged: {error_type} for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to log migration error: {e}")
        db.rollback()