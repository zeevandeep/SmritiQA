"""
Test script for OpenAI API integration.
"""
import os
import json
from openai import OpenAI

# Get API key from environment
api_key = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

def test_openai():
    """Test OpenAI API with a simple prompt."""
    print("=== Testing OpenAI API ===\n")
    
    # Simple test prompt
    prompt = """
    Analyze the following journal entry and identify distinct thought units, emotions, themes, and beliefs.
    Extract each thought as a separate unit with the following attributes:
    - text: The actual thought text
    - emotion: The primary emotion expressed
    - theme: The theme or topic
    - cognition_type: The type of thought (e.g., memory, belief, observation)
    - belief_value: Any core belief expressed
    - contradiction_flag: true if this thought contradicts another in the entry
    
    Format your response as a JSON object with a "nodes" key containing an array of thought objects.
    
    Journal Entry:
    Today was a mix of emotions. I felt proud when my presentation at work was well-received, 
    but later I became anxious about the upcoming deadline for the next project. 
    This deadline reminds me of a time I missed an important submission and disappointed my team.
    """
    
    try:
        print("Sending request to OpenAI API...")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert psychologist specialized in cognitive analysis."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            timeout=30  # Set a timeout of 30 seconds
        )
        
        print("Response received from OpenAI API.")
        response_content = response.choices[0].message.content
        print(f"Raw response: {response_content}")
        
        # Parse the response
        result = json.loads(response_content)
        
        # Check if the response has the expected format
        if "nodes" in result:
            nodes = result["nodes"]
            print(f"\nSuccessfully parsed {len(nodes)} nodes:")
            
            # Print a summary of each node
            for i, node in enumerate(nodes, 1):
                print(f"\nNode {i}:")
                print(f"  Text: {node['text'][:50]}..." if len(node['text']) > 50 else f"  Text: {node['text']}")
                print(f"  Emotion: {node.get('emotion', 'Not specified')}")
                print(f"  Theme: {node.get('theme', 'Not specified')}")
                print(f"  Cognition Type: {node.get('cognition_type', 'Not specified')}")
        else:
            print(f"Response doesn't contain 'nodes' key. Got: {list(result.keys())}")
    
    except Exception as e:
        print(f"Error testing OpenAI API: {e}")

if __name__ == "__main__":
    test_openai()