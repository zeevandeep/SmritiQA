#!/usr/bin/env python3
"""
Test to reproduce the JSON formatting issue with encrypted nodes.
This will help us compare OpenAI responses for encrypted vs unencrypted node processing.
"""

import sys
import os
import json
from typing import Dict, Any, List

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from utils.openai_utils import generate_reflection
from utils.encryption import encrypt_data, decrypt_data

def test_openai_response_consistency():
    """Test if OpenAI responds differently to encrypted vs unencrypted text"""
    
    # Test data - simulating the exact nodes from test7
    test_nodes = [
        {
            'id': '1',
            'text': 'While creating this MVP, we understood the scope of the app has to be more. We have to implement a lot more features so that users can use this application effectively.',
            'theme': 'career',
            'cognition_type': 'insight',
            'emotion': 'determined',
            'created_at': '2025-07-19T06:57:32'
        },
        {
            'id': '2', 
            'text': 'We have done a lot of meaningful work on this project. The reflection generation system is working well and users are getting value from their journal entries.',
            'theme': 'growth',
            'cognition_type': 'insight', 
            'emotion': 'inspired',
            'created_at': '2025-07-19T06:57:32'
        }
    ]
    
    print("=== Testing OpenAI Response Consistency ===\n")
    
    # Test 1: Direct nodes (simulating unencrypted path)
    print("Test 1: Direct nodes (unencrypted simulation)")
    print("-" * 50)
    
    try:
        response1 = generate_reflection(test_nodes, [], 'en')
        print("Response 1 (Direct):")
        print(f"Type: {type(response1)}")
        print(f"Keys: {list(response1.keys()) if isinstance(response1, dict) else 'Not a dict'}")
        if isinstance(response1, dict):
            for key, value in response1.items():
                print(f"  {key}: {repr(value[:100])}..." if isinstance(value, str) and len(value) > 100 else f"  {key}: {repr(value)}")
        print()
    except Exception as e:
        print(f"Error in test 1: {e}")
        
    # Test 2: Simulate encrypted node processing path
    print("Test 2: Simulated encrypted path processing")
    print("-" * 50)
    
    # Create nodes that simulate the decryption process
    # (In reality, the text would be the same but would have gone through encrypt/decrypt cycle)
    user_id = '72c24fda-093c-4430-98d9-a884d8e872b6'
    
    simulated_encrypted_nodes = []
    for node in test_nodes:
        # Simulate encrypt -> decrypt cycle 
        try:
            encrypted_text = encrypt_data(node['text'], user_id)
            decrypted_text = decrypt_data(encrypted_text, user_id)
            
            # Create node with decrypted text (as would happen in the actual flow)
            encrypted_node = node.copy()
            encrypted_node['text'] = decrypted_text
            simulated_encrypted_nodes.append(encrypted_node)
            
            print(f"Original text: {repr(node['text'][:50])}...")
            print(f"After encrypt/decrypt: {repr(decrypted_text[:50])}...")
            print(f"Texts match: {node['text'] == decrypted_text}")
            print()
            
        except Exception as e:
            print(f"Error in encryption/decryption: {e}")
            return
    
    try:
        response2 = generate_reflection(simulated_encrypted_nodes, [], 'en')
        print("Response 2 (After Encrypt/Decrypt):")
        print(f"Type: {type(response2)}")
        print(f"Keys: {list(response2.keys()) if isinstance(response2, dict) else 'Not a dict'}")
        if isinstance(response2, dict):
            for key, value in response2.items():
                print(f"  {key}: {repr(value[:100])}..." if isinstance(value, str) and len(value) > 100 else f"  {key}: {repr(value)}")
        print()
    except Exception as e:
        print(f"Error in test 2: {e}")
    
    # Compare responses
    print("=== Comparison ===")
    print(f"Response 1 keys: {list(response1.keys()) if 'response1' in locals() and isinstance(response1, dict) else 'N/A'}")
    print(f"Response 2 keys: {list(response2.keys()) if 'response2' in locals() and isinstance(response2, dict) else 'N/A'}")
    
    if 'response1' in locals() and 'response2' in locals():
        print(f"Responses have same structure: {type(response1) == type(response2) and (not isinstance(response1, dict) or set(response1.keys()) == set(response2.keys()))}")

if __name__ == "__main__":
    test_openai_response_consistency()