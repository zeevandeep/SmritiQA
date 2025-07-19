"""
Encryption utilities for user-specific data protection.

This module provides functions to encrypt and decrypt sensitive user data
using user-specific keys derived from a master key and static salt.
"""

import os
import base64
import logging
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

class EncryptionError(Exception):
    """Custom exception for encryption-related errors."""
    pass

def _get_encryption_config() -> tuple[bytes, bytes]:
    """
    Get master key and static salt from environment variables.
    
    Returns:
        tuple: (master_key, static_salt) as bytes
        
    Raises:
        EncryptionError: If required environment variables are missing
    """
    master_key_b64 = os.environ.get("MASTER_ENCRYPTION_KEY")
    static_salt_b64 = os.environ.get("STATIC_ENCRYPTION_SALT")
    
    if not master_key_b64 or not static_salt_b64:
        raise EncryptionError("Missing encryption environment variables")
    
    try:
        master_key = base64.urlsafe_b64decode(master_key_b64.encode())
        static_salt = base64.urlsafe_b64decode(static_salt_b64.encode())
        return master_key, static_salt
    except Exception as e:
        raise EncryptionError(f"Invalid encryption configuration: {e}")

def _derive_user_key(user_id: str) -> bytes:
    """
    Derive user-specific encryption key from master key and user ID.
    
    Args:
        user_id: User identifier (string)
        
    Returns:
        bytes: 32-byte encryption key
        
    Raises:
        EncryptionError: If key derivation fails
    """
    try:
        # Ensure user_id is a string
        if isinstance(user_id, bytes):
            user_id = user_id.decode()
        user_id_str = str(user_id)
        
        master_key, static_salt = _get_encryption_config()
        
        # Combine static salt with user ID for user-specific derivation
        combined_salt = static_salt + user_id_str.encode()
        
        # Use PBKDF2 to derive encryption key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=combined_salt,
            iterations=100_000,
        )
        
        key = kdf.derive(master_key)
        return base64.urlsafe_b64encode(key)
        
    except Exception as e:
        logger.error(f"[ENCRYPTION FAIL] op=derive_key user_id={user_id} error={e}")
        raise EncryptionError(f"Key derivation failed: {e}")

def encrypt_data(data: str, user_id: str) -> str:
    """
    Encrypt data using user-specific encryption key.
    
    Args:
        data: Plain text data to encrypt
        user_id: User identifier for key derivation
        
    Returns:
        str: Base64-encoded encrypted data
        
    Raises:
        EncryptionError: If encryption fails
    """
    if not data:
        return data
        
    try:
        key = _derive_user_key(user_id)
        fernet = Fernet(key)
        encrypted_bytes = fernet.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_bytes).decode()
        
    except Exception as e:
        logger.error(f"[ENCRYPTION FAIL] op=encrypt user_id={user_id} error={e}")
        raise EncryptionError(f"Encryption failed: {e}")

def decrypt_data(encrypted_data: str, user_id: str) -> str:
    """
    Decrypt data using user-specific encryption key.
    
    Args:
        encrypted_data: Base64-encoded encrypted data
        user_id: User identifier for key derivation
        
    Returns:
        str: Decrypted plain text data
        
    Raises:
        EncryptionError: If decryption fails
    """
    if not encrypted_data:
        return encrypted_data
        
    try:
        key = _derive_user_key(user_id)
        fernet = Fernet(key)
        
        # Decode the base64 encrypted data
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
        
        # Decrypt and return as string
        decrypted_bytes = fernet.decrypt(encrypted_bytes)
        return decrypted_bytes.decode()
        
    except Exception as e:
        logger.error(f"[ENCRYPTION FAIL] op=decrypt user_id={user_id} error={e}")
        raise EncryptionError(f"Decryption failed: {e}")

def derive_user_key(user_id: str) -> bytes:
    """
    Public function to derive user-specific encryption key.
    
    Args:
        user_id: User identifier
        
    Returns:
        bytes: User-specific encryption key
        
    Raises:
        EncryptionError: If key derivation fails
    """
    return _derive_user_key(user_id)

def test_encryption_roundtrip(user_id: str, test_data: str = "Test encryption data") -> bool:
    """
    Test encryption/decryption roundtrip for a user.
    
    Args:
        user_id: User identifier
        test_data: Test data to encrypt/decrypt
        
    Returns:
        bool: True if roundtrip successful, False otherwise
    """
    try:
        encrypted = encrypt_data(test_data, user_id)
        decrypted = decrypt_data(encrypted, user_id)
        success = decrypted == test_data
        
        if success:
            logger.info(f"Encryption roundtrip test successful for user {user_id}")
        else:
            logger.error(f"Encryption roundtrip test failed for user {user_id}")
            
        return success
        
    except Exception as e:
        logger.error(f"Encryption roundtrip test error for user {user_id}: {e}")
        return False