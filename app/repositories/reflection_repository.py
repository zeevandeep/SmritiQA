"""
Reflection repository for database operations related to AI-generated reflections.
"""
import os
import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy import func
from sqlalchemy.orm import Session as DbSession

from app.models.models import Reflection, Node, Edge, MigrationError
from app.schemas.schemas import ReflectionCreate
from app.utils.encryption import encrypt_data, decrypt_data, EncryptionError

logger = logging.getLogger(__name__)


def create_reflection(db: DbSession, reflection: ReflectionCreate, encrypt: Optional[bool] = None) -> Reflection:
    """
    Create a new reflection with optional encryption based on environment settings.
    
    Args:
        db: Database session.
        reflection: Data for the new reflection.
        encrypt: Optional override for encryption setting. If None, uses ENCRYPT_NEW_REFLECTIONS env var.
        
    Returns:
        Created Reflection object.
    """
    logger.info(f"Creating new reflection for user {reflection.user_id}")
    
    # Check if encryption is enabled for new reflections
    if encrypt is None:
        encrypt_new_reflections = os.environ.get("ENCRYPT_NEW_REFLECTIONS", "false").lower() == "true"
    else:
        encrypt_new_reflections = encrypt
    
    logger.info(f"ENCRYPT_NEW_REFLECTIONS setting: {encrypt_new_reflections}")
    
    # Get the original text and user_id
    original_text = reflection.generated_text
    user_id_str = str(reflection.user_id)
    
    if encrypt_new_reflections and original_text:
        try:
            logger.info(f"Encrypting reflection text for user {user_id_str}, original length: {len(original_text)}")
            
            # Encrypt the generated text
            encrypted_text = encrypt_data(original_text, user_id_str)
            
            logger.info(f"Successfully encrypted reflection text for user {user_id_str}, encrypted length: {len(encrypted_text)}")
            
            # Create Reflection object DIRECTLY with encrypted data (like sessions)
            db_reflection = Reflection(
                user_id=reflection.user_id,
                node_ids=reflection.node_ids,
                edge_ids=reflection.edge_ids,
                generated_text=encrypted_text,  # Use encrypted data directly
                confidence_score=reflection.confidence_score,
                is_encrypted=True,
                is_reflected=False,
                is_viewed=False,
                feedback=None
            )
            
        except EncryptionError as e:
            logger.error(f"[ENCRYPTION FAIL] op=encrypt_reflection user_id={user_id_str} error={e}")
            # Log encryption error
            error_record = MigrationError(
                user_id=reflection.user_id,
                session_id=None,  # Reflections don't have session_id
                error_type="reflection_encryption_failed",
                error_message=f"Failed to encrypt reflection text: {str(e)}"
            )
            db.add(error_record)
            db.commit()
            
            # Create with unencrypted text as fallback
            db_reflection = Reflection(
                user_id=reflection.user_id,
                node_ids=reflection.node_ids,
                edge_ids=reflection.edge_ids,
                generated_text=original_text,  # Use plain text
                confidence_score=reflection.confidence_score,
                is_encrypted=False,
                is_reflected=False,
                is_viewed=False,
                feedback=None
            )
            logger.warning(f"Encryption failed for user {user_id_str}, storing reflection as plain text")
    else:
        # Encryption disabled or no text to encrypt
        db_reflection = Reflection(
            user_id=reflection.user_id,
            node_ids=reflection.node_ids,
            edge_ids=reflection.edge_ids,
            generated_text=original_text,
            confidence_score=reflection.confidence_score,
            is_encrypted=False,
            is_reflected=False,
            is_viewed=False,
            feedback=None
        )
        logger.info(f"Reflection encryption disabled or no text, storing as plain text")
    
    db.add(db_reflection)
    db.commit()
    db.refresh(db_reflection)
    
    logger.info(f"Successfully created reflection {db_reflection.id}, encrypted: {db_reflection.is_encrypted}")
    return db_reflection


def get_reflection(db: DbSession, reflection_id: UUID, decrypt_for_processing: bool = False) -> Optional[Reflection]:
    """
    Get a reflection by ID with optional decryption for processing.
    
    Args:
        db: Database session.
        reflection_id: ID of the reflection to retrieve.
        decrypt_for_processing: If True, returns detached object with decrypted data for OpenAI.
                               If False (default), returns attached SQLAlchemy object for normal operations.
        
    Returns:
        Reflection object (attached or detached based on decrypt_for_processing) if found, None otherwise.
    """
    logger.info(f"Getting reflection: {reflection_id}, decrypt_for_processing: {decrypt_for_processing}")
    
    db_reflection = db.query(Reflection).filter(Reflection.id == reflection_id).first()
    if not db_reflection:
        logger.warning(f"Reflection not found: {reflection_id}")
        return None
    
    logger.info(f"Found reflection {reflection_id}, is_encrypted: {db_reflection.is_encrypted}")
    
    # If requesting for processing, return attached SQLAlchemy object (may be encrypted)
    if decrypt_for_processing:
        if db_reflection.is_encrypted and db_reflection.generated_text:
            # For processing - return detached object with decrypted data
            try:
                user_id = str(db_reflection.user_id)
                logger.info(f"Decrypting reflection {reflection_id} for processing (user {user_id})")
                
                # Create a new Reflection object with decrypted data
                decrypted_text = decrypt_data(db_reflection.generated_text, user_id)
                
                decrypted_reflection = Reflection(
                    id=db_reflection.id,
                    user_id=db_reflection.user_id,
                    node_ids=db_reflection.node_ids,
                    edge_ids=db_reflection.edge_ids,
                    generated_text=decrypted_text,  # Use decrypted text
                    is_encrypted=db_reflection.is_encrypted,
                    generated_at=db_reflection.generated_at,
                    is_reflected=db_reflection.is_reflected,
                    is_viewed=db_reflection.is_viewed,
                    feedback=db_reflection.feedback,
                    confidence_score=db_reflection.confidence_score
                )
                
                logger.info(f"Successfully decrypted reflection {reflection_id} for processing, decrypted length: {len(decrypted_text)}")
                return decrypted_reflection
                
            except EncryptionError as e:
                logger.error(f"[ENCRYPTION FAIL] op=decrypt_reflection reflection_id={reflection_id} user_id={user_id} error={e}")
                # Return original encrypted reflection for fallback
                logger.warning(f"Decryption failed for reflection {reflection_id}, returning encrypted reflection")
                return db_reflection
        else:
            # For processing - unencrypted reflection
            logger.info(f"Returning unencrypted reflection {reflection_id} for processing")
            return db_reflection
    
    # For user display (default) - decrypt if encrypted
    if db_reflection.is_encrypted and db_reflection.generated_text:
        try:
            user_id = str(db_reflection.user_id)
            logger.info(f"Decrypting reflection {reflection_id} for user display (user {user_id})")
            
            # Decrypt the text for user display
            decrypted_text = decrypt_data(db_reflection.generated_text, user_id)
            
            # Create a new detached object for user display (don't modify attached object!)
            decrypted_reflection = Reflection(
                id=db_reflection.id,
                user_id=db_reflection.user_id,
                node_ids=db_reflection.node_ids,
                edge_ids=db_reflection.edge_ids,
                generated_text=decrypted_text,  # Use decrypted text
                is_encrypted=db_reflection.is_encrypted,
                generated_at=db_reflection.generated_at,
                is_reflected=db_reflection.is_reflected,
                is_viewed=db_reflection.is_viewed,
                feedback=db_reflection.feedback,
                confidence_score=db_reflection.confidence_score
            )
            
            logger.info(f"Successfully decrypted reflection {reflection_id} for user display, decrypted length: {len(decrypted_text)}")
            return decrypted_reflection
            
        except EncryptionError as e:
            logger.error(f"[ENCRYPTION FAIL] op=decrypt_reflection reflection_id={reflection_id} user_id={user_id} error={e}")
            # Log encryption error for review
            error_record = MigrationError(
                user_id=db_reflection.user_id,
                session_id=None,  # Reflections don't have session_id
                error_type="reflection_decryption_failed",
                error_message=f"Failed to decrypt reflection {reflection_id}: {str(e)}"
            )
            db.add(error_record)
            db.commit()
            
            # Return original encrypted reflection for fallback
            logger.warning(f"Decryption failed for reflection {reflection_id}, returning encrypted reflection")
            return db_reflection
    
    # For unencrypted reflections - return as-is for user display
    logger.info(f"Returning unencrypted reflection {reflection_id} for user display")
    return db_reflection


def get_user_reflections(
    db: DbSession,
    user_id: UUID,
    skip: int = 0,
    limit: int = 100,
    include_viewed: bool = True,
    decrypt_for_processing: bool = False
) -> List[Reflection]:
    """
    Get reflections for a user with optional decryption.
    
    Args:
        db: Database session.
        user_id: ID of the user.
        skip: Number of reflections to skip.
        limit: Maximum number of reflections to return.
        include_viewed: Whether to include reflections that have been viewed.
        decrypt_for_processing: If True, returns decrypted text for processing.
        
    Returns:
        List of Reflection objects with decrypted text if requested.
    """
    logger.info(f"Getting user reflections: user_id={user_id}, skip={skip}, limit={limit}, decrypt_for_processing={decrypt_for_processing}")
    
    query = db.query(Reflection).filter(Reflection.user_id == user_id)
    
    if not include_viewed:
        query = query.filter(Reflection.is_reflected == False)
    
    db_reflections = query.order_by(Reflection.generated_at.desc()).offset(skip).limit(limit).all()
    
    if not decrypt_for_processing:
        # For user-facing operations, decrypt for display (users should always see readable text)
        return _decrypt_reflections_for_user(db, db_reflections, str(user_id))
    
    # For processing operations, return with processing decryption
    return [get_reflection(db, reflection.id, decrypt_for_processing=True) for reflection in db_reflections if get_reflection(db, reflection.id, decrypt_for_processing=True)]


def _decrypt_reflections_for_user(db: DbSession, reflections: List[Reflection], user_id: str) -> List[Reflection]:
    """
    Helper function to decrypt reflections for user-facing operations (always return decrypted text).
    
    Args:
        db: Database session.
        reflections: List of Reflection objects to decrypt.
        user_id: User ID for decryption.
        
    Returns:
        List of Reflection objects with decrypted text for display.
    """
    decrypted_reflections = []
    
    for reflection in reflections:
        if reflection.is_encrypted and reflection.generated_text:
            try:
                logger.info(f"Decrypting reflection {reflection.id} for user display (user {user_id})")
                decrypted_text = decrypt_data(reflection.generated_text, user_id)
                
                # Create new reflection with decrypted text for display
                decrypted_reflection = Reflection(
                    id=reflection.id,
                    user_id=reflection.user_id,
                    node_ids=reflection.node_ids,
                    edge_ids=reflection.edge_ids,
                    generated_text=decrypted_text,
                    is_encrypted=reflection.is_encrypted,
                    generated_at=reflection.generated_at,
                    is_reflected=reflection.is_reflected,
                    is_viewed=reflection.is_viewed,
                    feedback=reflection.feedback,
                    confidence_score=reflection.confidence_score
                )
                decrypted_reflections.append(decrypted_reflection)
                logger.info(f"Successfully decrypted reflection {reflection.id} for user display")
                
            except EncryptionError as e:
                logger.error(f"[ENCRYPTION FAIL] op=decrypt_for_user reflection_id={reflection.id} user_id={user_id} error={e}")
                # Log encryption error
                error_record = MigrationError(
                    user_id=reflection.user_id,
                    session_id=None,  # Reflections don't have session_id
                    error_type="reflection_user_decryption_failed",
                    error_message=f"Failed to decrypt reflection {reflection.id} for user display: {str(e)}"
                )
                db.add(error_record)
                db.commit()
                
                # Skip this reflection (don't show corrupted encrypted reflections to user)
                logger.warning(f"Skipping corrupted encrypted reflection {reflection.id} for user {user_id}")
                continue
        else:
            # Unencrypted reflection or no text - include as-is
            decrypted_reflections.append(reflection)
    
    return decrypted_reflections


def get_user_reflection_count(db: DbSession, user_id: UUID) -> int:
    """
    Get the total count of reflections for a user.
    
    Args:
        db: Database session.
        user_id: ID of the user.
        
    Returns:
        Total count of reflections for the user.
    """
    return db.query(Reflection).filter(Reflection.user_id == user_id).count()


def get_reflections(
    db: DbSession,
    skip: int = 0,
    limit: int = 100,
    include_viewed: bool = True
) -> List[Reflection]:
    """
    Get all reflections across users.
    
    Args:
        db: Database session.
        skip: Number of reflections to skip.
        limit: Maximum number of reflections to return.
        include_viewed: Whether to include reflections that have been viewed.
        
    Returns:
        List of Reflection objects.
    """
    query = db.query(Reflection)
    
    if not include_viewed:
        query = query.filter(Reflection.is_reflected == False)
    
    return query.order_by(Reflection.generated_at.desc()).offset(skip).limit(limit).all()


def mark_reflection_viewed(db: DbSession, reflection_id: UUID) -> Optional[Reflection]:
    """
    Mark a reflection as having been viewed by the user.
    
    Args:
        db: Database session.
        reflection_id: ID of the reflection to mark.
        
    Returns:
        Updated Reflection object if found, None otherwise.
    """
    db_reflection = get_reflection(db, reflection_id)
    if db_reflection:
        # Use setattr to avoid direct attribute assignment LSP error
        setattr(db_reflection, 'is_reflected', True)
        db.commit()
        db.refresh(db_reflection)
    return db_reflection


def add_reflection_feedback(db: DbSession, reflection_id: UUID, feedback: int) -> Optional[Reflection]:
    """
    Add user feedback to a reflection.
    
    Args:
        db: Database session.
        reflection_id: ID of the reflection to update.
        feedback: Integer feedback value (1 for thumbs up, -1 for thumbs down).
        
    Returns:
        Updated Reflection object if found, None otherwise.
    """
    # Ensure feedback is a valid value
    if feedback not in [-1, 1]:
        raise ValueError("Feedback must be 1 (thumbs up) or -1 (thumbs down)")
        
    db_reflection = get_reflection(db, reflection_id)
    if db_reflection:
        # Use setattr to avoid direct attribute assignment LSP error
        setattr(db_reflection, 'feedback', feedback)
        db.commit()
        db.refresh(db_reflection)
    return db_reflection


def get_node_details(db: DbSession, node_ids: List[UUID]) -> List[Dict[str, Any]]:
    """
    Get details for a list of nodes.
    
    Args:
        db: Database session.
        node_ids: List of node IDs to retrieve.
        
    Returns:
        List of node details as dictionaries.
    """
    nodes = db.query(Node).filter(Node.id.in_(node_ids)).all()
    return [
        {
            "user_id": str(node.user_id),
            "text": node.text,
            "theme": node.theme,
            "cognition_type": node.cognition_type,
            "emotion": node.emotion,
            "created_at": node.created_at.isoformat()
        }
        for node in nodes
    ]


def get_edge_details(db: DbSession, edge_ids: List[UUID]) -> List[Dict[str, Any]]:
    """
    Get details for a list of edges.
    
    Args:
        db: Database session.
        edge_ids: List of edge IDs to retrieve.
        
    Returns:
        List of edge details as dictionaries.
    """
    edges = db.query(Edge).filter(Edge.id.in_(edge_ids)).all()
    return [
        {
            "edge_type": edge.edge_type,
            "match_strength": edge.match_strength,
            "explanation": edge.explanation
        }
        for edge in edges
    ]


def mark_edges_processed(db: DbSession, edge_ids: List[UUID]) -> int:
    """
    Mark edges as processed.
    
    Args:
        db: Database session.
        edge_ids: List of edge IDs to mark as processed.
        
    Returns:
        Number of edges marked as processed.
    """
    result = db.query(Edge).filter(Edge.id.in_(edge_ids)).update(
        {"is_processed": True},
        synchronize_session=False
    )
    db.commit()
    return result