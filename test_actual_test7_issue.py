#!/usr/bin/env python3
"""
Test with actual test7 user data to see what causes the JSON formatting issue.
"""

import sys
import os
import json
from uuid import UUID

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database import get_db
from app.repositories import node_repository, user_repository
from app.services.reflection_processor import generate_reflection_for_user

def test_actual_test7_reflection():
    """Test reflection generation for actual test7 user"""
    
    test7_user_id = UUID('72c24fda-093c-4430-98d9-a884d8e872b6')
    
    print("=== Testing Actual test7 User Reflection ===\n")
    
    with get_db() as db:
        # Get test7's user profile to check language
        user_profile = user_repository.get_user_profile(db, test7_user_id)
        if user_profile:
            user_language = user_profile.language or 'en'
            print(f"User language: {user_language}")
        else:
            user_language = 'en'
            print("No user profile found, using default language: en")
        
        # Get test7's nodes with decryption
        nodes = node_repository.get_user_nodes(db, test7_user_id, decrypt_for_processing=True)
        print(f"Found {len(nodes)} nodes for test7")
        
        if nodes:
            # Show the first few nodes
            for i, node in enumerate(nodes[:3]):
                print(f"Node {i+1}: {repr(node.text[:60])}... (encrypted: {node.is_encrypted})")
        
        print("\n" + "="*50)
        print("Generating reflection...")
        print("="*50)
        
        try:
            # Generate reflection using the actual service
            reflection_result = generate_reflection_for_user(db, test7_user_id)
            
            print(f"Reflection result type: {type(reflection_result)}")
            print(f"Reflection result: {reflection_result}")
            
            if isinstance(reflection_result, dict):
                print(f"Keys: {list(reflection_result.keys())}")
                for key, value in reflection_result.items():
                    if isinstance(value, str):
                        print(f"{key}: {repr(value[:100])}...")
                        # Check for formatting issues
                        if '\\n\\n' in value:
                            print(f"  WARNING: Found literal \\n\\n in {key}")
                        if value.startswith('{"') and value.endswith('"}'):
                            print(f"  WARNING: {key} appears to be JSON-wrapped")
                    else:
                        print(f"{key}: {value}")
                        
        except Exception as e:
            print(f"Error generating reflection: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_actual_test7_reflection()