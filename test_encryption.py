#!/usr/bin/env python3
"""
Test script to verify encryption system is working correctly.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.encryption import test_encryption_roundtrip, encrypt_data, decrypt_data, EncryptionError

def test_encryption_functionality():
    """Test encryption functionality with sample data."""
    print("Testing encryption system...")
    print("=" * 50)
    
    # Test user ID
    test_user_id = "bd1c76c9-1b6d-440f-8b09-6ba917789f44"
    
    # Test data
    test_transcript = "This is a test journal entry with sensitive personal information."
    
    try:
        # Test encryption roundtrip
        print(f"Testing encryption roundtrip for user: {test_user_id}")
        success = test_encryption_roundtrip(test_user_id, test_transcript)
        
        if success:
            print("✓ Encryption roundtrip test PASSED")
        else:
            print("✗ Encryption roundtrip test FAILED")
            return False
        
        # Test manual encryption/decryption
        print("\nTesting manual encryption/decryption...")
        
        # Encrypt
        encrypted = encrypt_data(test_transcript, test_user_id)
        print(f"Original: {test_transcript}")
        print(f"Encrypted: {encrypted[:50]}...")
        
        # Decrypt
        decrypted = decrypt_data(encrypted, test_user_id)
        print(f"Decrypted: {decrypted}")
        
        # Verify they match
        if decrypted == test_transcript:
            print("✓ Manual encryption/decryption test PASSED")
        else:
            print("✗ Manual encryption/decryption test FAILED")
            return False
        
        # Test with different user ID (should fail)
        print("\nTesting with different user ID...")
        different_user_id = "12345678-1234-1234-1234-123456789012"
        
        try:
            wrong_decrypt = decrypt_data(encrypted, different_user_id)
            print("✗ Security test FAILED - different user could decrypt data")
            return False
        except EncryptionError:
            print("✓ Security test PASSED - different user cannot decrypt data")
        
        print("\n" + "=" * 50)
        print("All encryption tests PASSED!")
        return True
        
    except Exception as e:
        print(f"✗ Encryption test FAILED with error: {e}")
        return False

if __name__ == "__main__":
    success = test_encryption_functionality()
    sys.exit(0 if success else 1)