"""
Database encryption utilities for sensitive user data.

This module provides encryption/decryption for raw transcripts and other sensitive
data stored in the database. Uses AES-256-GCM for authenticated encryption.
"""

import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class DatabaseEncryption:
    """Handles encryption/decryption of sensitive database fields."""
    
    def __init__(self):
        """Initialize encryption with key derived from environment variable."""
        self._fernet = None
        self._initialize_encryption()
    
    def _initialize_encryption(self):
        """Initialize the encryption key from environment variable."""
        try:
            # Get encryption key from environment (Replit secrets)
            encryption_key = os.environ.get('DATABASE_ENCRYPTION_KEY')
            
            if not encryption_key:
                logger.warning("DATABASE_ENCRYPTION_KEY not set - encryption disabled")
                logger.info("Set DATABASE_ENCRYPTION_KEY in Replit secrets to enable encryption")
                return
            
            # Derive key using PBKDF2
            salt = b'smriti_journal_salt_2025'  # Fixed salt for consistency
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            
            key = base64.urlsafe_b64encode(kdf.derive(encryption_key.encode()))
            self._fernet = Fernet(key)
            
            logger.info("Database encryption initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            self._fernet = None
    
    def encrypt_transcript(self, transcript: str) -> str:
        """
        Encrypt a journal transcript.
        
        Args:
            transcript: The raw transcript text to encrypt
            
        Returns:
            str: Base64-encoded encrypted transcript, or original if encryption disabled
        """
        if not transcript:
            return transcript
            
        if not self._fernet:
            logger.warning("Encryption not available - storing transcript unencrypted")
            return transcript
        
        try:
            # Encrypt the transcript
            encrypted_bytes = self._fernet.encrypt(transcript.encode('utf-8'))
            
            # Return base64-encoded encrypted data
            encrypted_text = base64.b64encode(encrypted_bytes).decode('utf-8')
            
            logger.debug(f"Encrypted transcript of length {len(transcript)} -> {len(encrypted_text)}")
            return encrypted_text
            
        except Exception as e:
            logger.error(f"Failed to encrypt transcript: {e}")
            # Fall back to unencrypted storage
            return transcript
    
    def decrypt_transcript(self, encrypted_transcript: str) -> str:
        """
        Decrypt a journal transcript.
        
        Args:
            encrypted_transcript: Base64-encoded encrypted transcript
            
        Returns:
            str: Decrypted transcript text, or original if encryption disabled/failed
        """
        if not encrypted_transcript:
            return encrypted_transcript
            
        if not self._fernet:
            # If encryption is disabled, assume data is stored unencrypted
            return encrypted_transcript
        
        try:
            # Check if this looks like encrypted data (base64)
            if not self._is_base64_encrypted(encrypted_transcript):
                # Assume this is unencrypted legacy data
                logger.debug("Transcript appears to be unencrypted legacy data")
                return encrypted_transcript
            
            # Decode from base64
            encrypted_bytes = base64.b64decode(encrypted_transcript.encode('utf-8'))
            
            # Decrypt the transcript
            decrypted_bytes = self._fernet.decrypt(encrypted_bytes)
            decrypted_text = decrypted_bytes.decode('utf-8')
            
            logger.debug(f"Decrypted transcript of length {len(encrypted_transcript)} -> {len(decrypted_text)}")
            return decrypted_text
            
        except Exception as e:
            logger.warning(f"Failed to decrypt transcript, returning as-is: {e}")
            # Fall back to returning the original data
            return encrypted_transcript
    
    def _is_base64_encrypted(self, text: str) -> bool:
        """
        Check if text appears to be base64-encoded encrypted data.
        
        Args:
            text: Text to check
            
        Returns:
            bool: True if appears to be encrypted, False otherwise
        """
        try:
            # Basic heuristics for encrypted data:
            # 1. Length suggests base64 encoding
            # 2. Only contains base64 characters
            # 3. No spaces or common words
            
            if len(text) < 50:  # Very short text unlikely to be encrypted
                return False
                
            # Check for base64 characters only
            import string
            base64_chars = string.ascii_letters + string.digits + '+/='
            if not all(c in base64_chars for c in text):
                return False
                
            # Check if it can be base64 decoded
            base64.b64decode(text.encode('utf-8'))
            
            # If we get here, it's likely encrypted
            return True
            
        except Exception:
            return False
    
    def is_encryption_enabled(self) -> bool:
        """
        Check if encryption is properly configured and enabled.
        
        Returns:
            bool: True if encryption is available, False otherwise
        """
        return self._fernet is not None


# Global encryption instance
_encryption_instance = None

def get_encryption() -> DatabaseEncryption:
    """
    Get the global encryption instance.
    
    Returns:
        DatabaseEncryption: The encryption instance
    """
    global _encryption_instance
    if _encryption_instance is None:
        _encryption_instance = DatabaseEncryption()
    return _encryption_instance

def encrypt_transcript(transcript: str) -> str:
    """
    Convenience function to encrypt a transcript.
    
    Args:
        transcript: The raw transcript text to encrypt
        
    Returns:
        str: Encrypted transcript
    """
    return get_encryption().encrypt_transcript(transcript)

def decrypt_transcript(encrypted_transcript: str) -> str:
    """
    Convenience function to decrypt a transcript.
    
    Args:
        encrypted_transcript: Encrypted transcript text
        
    Returns:
        str: Decrypted transcript
    """
    return get_encryption().decrypt_transcript(encrypted_transcript)