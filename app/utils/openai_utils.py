"""
OpenAI integration utilities for Smriti.

This module provides functions for interacting with the OpenAI API
to analyze text, extract emotions, generate reflections, etc.
"""
import json
import logging
import os
import time
import numpy as np
from typing import Dict, List, Any, Optional, Union
from openai import OpenAI
from pathlib import Path

from app.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client with API key from settings
client = OpenAI(api_key=settings.OPENAI_API_KEY)

# Define constants
EMBEDDING_MODEL = "text-embedding-ada-002"
DEFAULT_BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "50"))

# Edge creation thresholds and parameters
INITIAL_SIMILARITY_THRESHOLD = float(os.environ.get("INITIAL_SIMILARITY_THRESHOLD", "0.7"))
FINAL_SIMILARITY_THRESHOLD = float(os.environ.get("FINAL_SIMILARITY_THRESHOLD", "0.84"))
OPENAI_CONFIDENCE_THRESHOLD = float(os.environ.get("OPENAI_CONFIDENCE_THRESHOLD", "0.85"))

# Session window parameters
MAX_SESSIONS_TO_CONSIDER = int(os.environ.get("MAX_SESSIONS_TO_CONSIDER", "25"))
MAX_DAYS_TO_CONSIDER = int(os.environ.get("MAX_DAYS_TO_CONSIDER", "30"))
MAX_CANDIDATE_NODES = int(os.environ.get("MAX_CANDIDATE_NODES", "12"))

# Boost and penalty factors
THEME_MATCH_BOOST = float(os.environ.get("THEME_MATCH_BOOST", "0.1"))
COGNITION_MATCH_BOOST = float(os.environ.get("COGNITION_MATCH_BOOST", "0.1"))
EMOTION_MATCH_BOOST = float(os.environ.get("EMOTION_MATCH_BOOST", "0.05"))

THEME_MISMATCH_PENALTY = float(os.environ.get("THEME_MISMATCH_PENALTY", "0.1"))
COGNITION_MISMATCH_PENALTY = float(os.environ.get("COGNITION_MISMATCH_PENALTY", "0.1"))
EMOTION_MISMATCH_PENALTY = float(os.environ.get("EMOTION_MISMATCH_PENALTY", "0.05"))

# Temporal boost/penalty factors
RECENT_NODE_BOOST = float(os.environ.get("RECENT_NODE_BOOST", "0.05"))
OLDER_NODE_PENALTY = float(os.environ.get("OLDER_NODE_PENALTY", "0.05"))
RECENT_DAYS_THRESHOLD = int(os.environ.get("RECENT_DAYS_THRESHOLD", "7"))
OLDER_DAYS_THRESHOLD = int(os.environ.get("OLDER_DAYS_THRESHOLD", "30"))

# Edge limits per node
MAX_EDGES_PER_NODE = int(os.environ.get("MAX_EDGES_PER_NODE", "8"))


def extract_nodes_from_transcript(transcript: str) -> List[Dict[str, Any]]:
    """
    Extract atomic thought units (nodes) from a transcript.
    
    Args:
        transcript: The raw transcript text from a user session.
        
    Returns:
        List of dictionaries containing extracted nodes with their attributes.
    """
    logger.info(f"Extracting nodes from transcript of length: {len(transcript)}")
    
    # 🚫 UNIFIED NODE CREATION PROMPT - DO NOT MODIFY
    prompt = f"""
    You are processing a raw text from a journaling session. The goal is to extract multiple structured nodes, each representing a distinct theme or cognitive-emotional pattern. Use the controlled lists of themes, cognition types, and emotions provided. Each node must represent a **single theme**, a **dominant cognitive frame**, and a **dominant emotional tone**.

    ---
    Session Text:
    "{transcript}"
    ---
    Themes (Max 1 node per theme):  
    ["relationships", "career", "self-worth", "family", "health", "purpose", "money", "identity", "growth", "change", "conflict", "spirituality", "creativity", "freedom", "generic"]

    Cognition Types:  
    ["decision_intent", "self_reflection", "emotion_insight", "identity_question", "future_projection", "regret", "justification", "resignation", "generic"]

    Emotions:  
    ["hopeful", "content", "inspired", "determined", "grateful", "peaceful", "anxious", "fearful", "frustrated", "disconnected", "insecure", "doubtful", "generic"]

    ---

    ### Instructions

    1. **Node Segmentation:**  
       Break the journal into distinct, coherent **nodes**, each centered on a **single theme**. A node may span multiple sentences if they express a unified thought.

    2. **Theme Deduplication:**  
       Each theme should appear **only once**. If multiple passages relate to the same theme, choose the **most emotionally significant or contextually rich** segment.

    3. **Emotion Inference:**  
       Assign the **dominant emotional tone** of the node based on the entire segment. Do not rely on surface words — infer emotion from context and meaning. Use only the emotions listed.

    4. **Cognition Type Assignment:**  
       Assign the cognition type that best describes the mental function of the passage:
       - Why is this being said?
       - What kind of reflection, intent, or insight is happening?

    5. **No Redundancy:**  
       - A sentence should belong to **only one node**
       - No duplicate theme nodes
       - Avoid breaking the same thought into different nodes even if parts match different themes

    6. **Fallback Handling:**  
       If a passage is too ambiguous to match a known theme, cognition type, or emotion, use **"generic"** — but only when truly unavoidable.

    7. **Output Format:**  
       Return your output in this **exact JSON format**:
    ```json
    {{
      "nodes": [
        {{
          "text": "...",
          "theme": "...",
          "cognition_type": "...",
          "emotion": "..."
        }}
      ]
    }}
    ```
    """
    
    try:
        logger.info("Sending request to OpenAI API...")
        start_time = time.time()
        
        response = client.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            messages=[
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}, 
            max_tokens=2000
        )
        
        elapsed_time = time.time() - start_time
        logger.info(f"OpenAI API response received in {elapsed_time:.2f} seconds")
        
        # Parse the response
        response_content = response.choices[0].message.content
        logger.info(f"Raw response content: {response_content[:200]}...")
        
        result = json.loads(response_content)
        
        # Check the format of the result
        if isinstance(result, list):
            # New format: direct array of nodes
            logger.info(f"Received array of {len(result)} nodes")
            return result
        elif "nodes" in result:
            # Support for legacy format with "nodes" key
            logger.info(f"Found 'nodes' key in response with {len(result['nodes'])} nodes")
            return result["nodes"]
        
        logger.info(f"Unexpected response format, converting to usable format: {type(result)}")
        # If it's neither an array nor has a "nodes" key, try to extract a usable result
        # This is a fallback in case the model doesn't follow instructions exactly
        if isinstance(result, dict):
            # Try to find any array in the response that might contain the nodes
            for key, value in result.items():
                if isinstance(value, list) and value and isinstance(value[0], dict):
                    logger.info(f"Found potential nodes array under key '{key}' with {len(value)} items")
                    return value
        
        # Last resort: if it's a dict, wrap it in a list
        if isinstance(result, dict) and "text" in result:
            logger.info(f"Converting single node object to list")
            return [result]
            
        logger.warning(f"Could not extract nodes from response: {type(result)}")
        return []
    except Exception as e:
        # Log the error and return an empty list
        logger.error(f"Error extracting nodes from transcript: {e}", exc_info=True)
        return []


def create_edges_between_nodes(current_node: Dict[str, Any], candidate_nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Analyze the relationship between a current node and multiple candidate nodes and create edges.
    
    Args:
        current_node: The current node being processed.
        candidate_nodes: A list of candidate nodes that might form edges with the current node.
        
    Returns:
        List of dictionaries containing edge attributes for each valid connection.
    """
    logger.info(f"Creating edges for current node: {current_node.get('id', 'unknown')} with {len(candidate_nodes)} candidates")
    
    # Formatting the prompt with the current node and all candidate nodes
    prompt = "📝 Edge Creation Prompt (Optimized for Node Metadata)\n\n"
    prompt += "You are identifying meaningful psychological connections between pairs of thought nodes. "
    prompt += "Use the provided nodes and their attributes to classify the relationship type. "
    prompt += "Focus on identifying transitions, contradictions, and ongoing themes.\n\n"
    
    prompt += "---\n\n"
    
    # Current node information
    prompt += f"Current Node:  \n"
    prompt += f"- Node ID: {current_node.get('id')}  \n"
    prompt += f"- Text: \"{current_node.get('text', '')}\"  \n"
    prompt += f"- Theme: {current_node.get('theme', 'generic')}  \n"
    prompt += f"- Cognition Type: {current_node.get('cognition_type', 'generic')}  \n"
    prompt += f"- Emotion: {current_node.get('emotion', 'generic')}  \n\n"
    
    prompt += "---\n\n"
    
    # Candidate nodes information
    prompt += "Candidate Nodes:  \n"
    for i, node in enumerate(candidate_nodes, 1):
        prompt += f"{i}. Node ID: {node.get('id')}  \n"
        prompt += f"   - Text: \"{node.get('text', '')}\"  \n"
        prompt += f"   - Theme: {node.get('theme', 'generic')}  \n"
        prompt += f"   - Cognition Type: {node.get('cognition_type', 'generic')}  \n"
        prompt += f"   - Emotion: {node.get('emotion', 'generic')}  \n\n"
    
    prompt += "---\n\n"
    
    # Edge types
    prompt += "Edge Types (7 Total):  \n"
    prompt += "- thought_progression: One thought logically follows another.  \n"
    prompt += "- emotion_shift: A significant change in emotional tone.  \n"
    prompt += "- theme_repetition: Recurring themes across different contexts.  \n"
    prompt += "- identity_drift: Shifts in self-concept or core beliefs.  \n"
    prompt += "- emotional_contradiction: Conflicting emotions about the same topic.  \n"
    prompt += "- belief_contradiction: Inconsistent or opposing beliefs.  \n"
    prompt += "- unresolved_loop: Repeating patterns without resolution.  \n\n"
    
    prompt += "---\n\n"
    
    # Instructions
    prompt += "Instructions:  \n"
    prompt += "1. Identify meaningful edges based on the natural psychological connection between the Current Node and each Candidate Node.  \n"
    prompt += "2. Select the most contextually significant connection type from the fixed list above.  \n"
    prompt += "3. Provide a Confidence Score (0.0 to 1.0) indicating the strength of the connection.  \n"
    prompt += "4. Filter the results to only include edges where the match_strength is 0.7 or higher.  \n"
    prompt += "5. Return the results in JSON format with each edge containing:  \n"
    prompt += "   a. candidate_index - The number of the candidate node (as shown in the list above, e.g., 1, 2, 3, etc.)  \n"
    prompt += "   b. from_node_id - The ID of the candidate node (e.g., 12345-abcde-67890)  \n"
    prompt += "   c. to_node_id - The ID of the current node  \n"
    prompt += "   d. edge_type - One of the edge types from the list above  \n"
    prompt += "   e. match_strength - A float between 0.0 and 1.0  \n"
    prompt += "   f. explanation - A brief explanation of the connection  \n\n"
    
    # Session relation information
    session_relations = {}
    for node in candidate_nodes:
        is_same_session = node.get('session_id') == current_node.get('session_id')
        session_relations[str(node.get('id'))] = 'intra_session' if is_same_session else 'cross_session'
    
    # Maximum retry attempts for API call
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            logger.info(f"Sending edge creation request to OpenAI API (attempt {retry_count + 1}/{max_retries})...")
            start_time = time.time()
            
            response = client.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
                messages=[
                    {"role": "system", "content": "You are an expert in cognitive psychology and emotional analysis."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            elapsed_time = time.time() - start_time
            logger.info(f"Edge creation response received in {elapsed_time:.2f} seconds")
            
            # Parse the response
            response_content = response.choices[0].message.content
            result = json.loads(response_content)
            
            # Ensure the result is a list
            if not isinstance(result, list):
                if isinstance(result, dict) and any(key.startswith("from_node") for key in result.keys()):
                    # Single edge returned as dict
                    result = [result]
                elif isinstance(result, dict) and "edges" in result:
                    # Dict with "edges" key containing a list of edges
                    logger.info(f"Found 'edges' key in response with {len(result['edges'])} edges")
                    result = result["edges"]
                elif isinstance(result, dict) and "connections" in result:
                    # Dict with "connections" key containing a list of edges
                    logger.info(f"Found 'connections' key in response with {len(result['connections'])} edges")
                    result = result["connections"]
                elif isinstance(result, dict) and "results" in result:
                    # Dict with "results" key containing a list of edges
                    logger.info(f"Found 'results' key in response with {len(result['results'])} edges")
                    result = result["results"] 
                else:
                    # Try to find any array in the response that might contain the edges
                    found_edges = False
                    for key, value in result.items():
                        if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                            if any(edge_key in value[0] for edge_key in ["edge_type", "from_node_id", "to_node_id", "match_strength"]):
                                logger.info(f"Found potential edges array under key '{key}' with {len(value)} items")
                                result = value
                                found_edges = True
                                break
                    
                    if not found_edges:
                        logger.warning(f"Unexpected response format: {type(result)}")
                        result = []
            
            # Process and clean up edge data
            for edge in result:
                # Check if the edge has node_id, id, or similar keys instead of from_node_id
                if not edge.get("from_node_id") and edge.get("candidate_node_id"):
                    edge["from_node_id"] = edge.get("candidate_node_id")
                elif not edge.get("from_node_id") and edge.get("node_id"):
                    edge["from_node_id"] = edge.get("node_id")
                elif not edge.get("from_node_id") and edge.get("id"):
                    edge["from_node_id"] = edge.get("id")
                
                # Try to extract from candidate index if available
                if not edge.get("from_node_id") and edge.get("candidate_index") is not None:
                    try:
                        # First, try as an integer directly
                        idx = int(edge.get("candidate_index")) - 1  # Convert 1-based to 0-based index
                        if 0 <= idx < len(candidate_nodes):
                            edge["from_node_id"] = candidate_nodes[idx].get("id")
                    except (ValueError, TypeError):
                        # If that fails, see if it's in a format like "Candidate 3" or "Node 3"
                        candidate_str = str(edge.get("candidate_index"))
                        if any(prefix in candidate_str.lower() for prefix in ["candidate", "node"]):
                            try:
                                # Try to extract a number from the string
                                import re
                                numbers = re.findall(r'\d+', candidate_str)
                                if numbers:
                                    idx = int(numbers[0]) - 1
                                    if 0 <= idx < len(candidate_nodes):
                                        edge["from_node_id"] = candidate_nodes[idx].get("id") 
                            except (ValueError, TypeError):
                                pass
                
                # Try to match based on text content if available
                if not edge.get("from_node_id") and edge.get("text"):
                    matching_nodes = [
                        node.get("id") for node in candidate_nodes 
                        if node.get("text") and edge.get("text") in node.get("text")
                    ]
                    if matching_nodes:
                        edge["from_node_id"] = matching_nodes[0]
                
                # Add session relation if from_node_id is available
                from_node_id = edge.get("from_node_id")
                if isinstance(from_node_id, str):
                    edge['session_relation'] = session_relations.get(from_node_id, 'cross_session')
                
                # Ensure match_strength is a float
                if "match_strength" in edge:
                    try:
                        edge["match_strength"] = float(edge["match_strength"])
                    except (ValueError, TypeError):
                        edge["match_strength"] = 0.0
                else:
                    edge["match_strength"] = 0.0
                
                # Make sure explanation field is preserved
                if "explanation" not in edge or not edge["explanation"]:
                    # Check for alternative field names that might contain explanations
                    for field in ["reasoning", "reason", "description", "details", "justification", "rationale", "note", "notes"]:
                        if field in edge and edge[field]:
                            edge["explanation"] = edge[field]
                            break
                    else:
                        # If no explanation is found, create a generic one
                        edge_type = edge.get("edge_type", "connection")
                        strength = edge.get("match_strength", 0.0)
                        edge["explanation"] = f"This {edge_type} has a match strength of {strength:.2f}."
            
            # Filter edges with match_strength >= 0.7
            filtered_result = [edge for edge in result if edge.get("match_strength", 0) >= 0.7]
            logger.info(f"Filtered {len(filtered_result)} edges with match_strength >= 0.7 from {len(result)} total edges")
            return filtered_result
            
        except Exception as e:
            retry_count += 1
            logger.error(f"Error in edge creation attempt {retry_count}/{max_retries}: {e}", exc_info=True)
            if retry_count >= max_retries:
                logger.error("Maximum retry attempts reached, returning empty edge list")
                return []
            time.sleep(2)  # Short delay before retrying
    
    # This should not be reached due to the return in the exception handler
    return []


def generate_reflection(nodes: List[Dict[str, Any]], edges: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Generate a reflection based on a set of nodes and optional edges.
    
    Args:
        nodes: The list of nodes to generate a reflection for.
        edges: Optional list of edges between the nodes.
        
    Returns:
        Dictionary containing the generated reflection and confidence score.
    """
    logger.info(f"Generating reflection for {len(nodes)} nodes")
    
    # Extract node details
    thought_sequence = " -> ".join([node.get('text', '') for node in nodes])
    
    # Extract edge information if available
    connection_types = ""
    if edges and len(edges) > 0:
        edge_types = [edge.get('edge_type', 'unknown') for edge in edges]
        connection_types = f"\nConnection Types: {', '.join(edge_types)}"
        logger.info(f"Including {len(edges)} edges in reflection")
    
    # Collect themes and emotions
    themes = [node.get('theme', '') for node in nodes if node.get('theme')]
    emotions = [node.get('emotion', '') for node in nodes if node.get('emotion')]
    
    context_info = ""
    if themes:
        context_info += f"\nThemes: {', '.join(themes)}"
    if emotions:
        context_info += f"\nEmotions: {', '.join(emotions)}"
    
    prompt = f"""
    Based on the following sequence of thoughts, generate a thoughtful reflection.
    
    Thought Sequence: {thought_sequence}
    {connection_types}
    {context_info}
    
    Your reflection should:
    1. Identify patterns in the person's thinking
    2. Note any contradictions or emotional shifts
    3. Offer a perspective that might be helpful for self-awareness
    4. Be empathetic and non-judgmental
    5. Include a confidence score (0.0 to 1.0) about how meaningful this reflection is
    
    Format your response as a JSON object with generated_text and confidence_score fields.
    """
    
    try:
        logger.info("Sending reflection generation request to OpenAI API...")
        start_time = time.time()
        
        response = client.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            messages=[
                {"role": "system", "content": "You are an empathetic and insightful therapist."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        elapsed_time = time.time() - start_time
        logger.info(f"Reflection generation response received in {elapsed_time:.2f} seconds")
        
        # Parse the response
        response_content = response.choices[0].message.content
        result = json.loads(response_content)
        
        logger.info(f"Generated reflection with confidence score: {result.get('confidence_score')}")
        return result
    except Exception as e:
        # Log the error and return a default reflection
        logger.error(f"Error generating reflection: {e}", exc_info=True)
        return {
            "generated_text": "I noticed a pattern in your thoughts that might be worth reflecting on. Consider revisiting these ideas when you're ready.",
            "confidence_score": 0.3
        }


def generate_embedding(text: str) -> List[float]:
    """
    Generate an embedding vector for a single text.
    
    Args:
        text: The text to create an embedding for.
        
    Returns:
        A list of floats representing the embedding vector.
    """
    try:
        logger.info(f"Generating embedding for text of length: {len(text)}")
        start_time = time.time()
        
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text
        )
        
        elapsed_time = time.time() - start_time
        logger.info(f"Embedding generated in {elapsed_time:.2f} seconds")
        
        embedding = response.data[0].embedding
        return embedding
    except Exception as e:
        logger.error(f"Error generating embedding: {e}", exc_info=True)
        return []


def generate_embeddings_batch(texts: List[str]) -> List[Optional[List[float]]]:
    """
    Generate embeddings for a batch of texts.
    
    Args:
        texts: List of texts to create embeddings for.
        
    Returns:
        List of embedding vectors (as lists of floats).
    """
    if not texts:
        return []
    
    logger.info(f"Generating embeddings for batch of {len(texts)} texts")
    try:
        start_time = time.time()
        
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=texts
        )
        
        elapsed_time = time.time() - start_time
        logger.info(f"Batch embeddings generated in {elapsed_time:.2f} seconds")
        
        # Extract embeddings from response in the correct order
        embeddings = [data.embedding for data in response.data]
        return embeddings
    except Exception as e:
        logger.error(f"Error generating batch embeddings: {e}", exc_info=True)
        # Return empty embeddings for all texts
        return [None] * len(texts)


def serialize_embedding(embedding: List[float]) -> bytes:
    """
    Convert embedding vector to bytes for storage in database.
    
    Args:
        embedding: List of floats representing the embedding vector.
        
    Returns:
        Bytes representation of the embedding.
    """
    if not embedding:
        return b''
    
    try:
        return np.array(embedding, dtype=np.float32).tobytes()
    except Exception as e:
        logger.error(f"Error serializing embedding: {e}", exc_info=True)
        return b''


def deserialize_embedding(embedding_bytes: bytes) -> Optional[List[float]]:
    """
    Convert bytes from database back to embedding vector.
    
    Args:
        embedding_bytes: Bytes representation of the embedding.
        
    Returns:
        List of floats representing the embedding vector, or None if conversion fails.
    """
    if not embedding_bytes:
        return None
    
    try:
        embedding_array = np.frombuffer(embedding_bytes, dtype=np.float32)
        return embedding_array.tolist()
    except Exception as e:
        logger.error(f"Error deserializing embedding: {e}", exc_info=True)
        return None


def get_emotional_family(emotion: str) -> Optional[str]:
    """
    Get the emotional family for a given emotion based on predefined families.
    
    Args:
        emotion: The emotion to categorize.
        
    Returns:
        The name of the emotional family, or None if not found.
    """
    if not emotion:
        return None
    
    try:
        # Path to emotional families JSON file
        json_path = Path(__file__).parent / "emotional_families.json"
        
        # Load emotional families from the JSON file
        with open(json_path, "r") as f:
            emotional_families = json.load(f)
        
        # Normalize emotion (lowercase)
        normalized_emotion = emotion.lower()
        
        # Find the matching emotional family
        for family, emotions in emotional_families.items():
            if normalized_emotion in [e.lower() for e in emotions]:
                logger.info(f"Emotion '{emotion}' belongs to the '{family}' family")
                return family
        
        logger.warning(f"No emotional family found for emotion: {emotion}")
        return None
    except Exception as e:
        logger.error(f"Error getting emotional family: {e}", exc_info=True)
        return None


def calculate_cosine_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    """
    Calculate cosine similarity between two embedding vectors.
    
    Args:
        embedding1: First embedding vector.
        embedding2: Second embedding vector.
        
    Returns:
        The cosine similarity score between 0 and 1.
    """
    if not embedding1 or not embedding2:
        return 0.0
    
    try:
        # Convert to numpy arrays
        a = np.array(embedding1)
        b = np.array(embedding2)
        
        # Calculate cosine similarity
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        # Avoid division by zero
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        similarity = dot_product / (norm_a * norm_b)
        return float(similarity)
    except Exception as e:
        logger.error(f"Error calculating cosine similarity: {e}", exc_info=True)
        return 0.0


def calculate_adjusted_similarity(
    base_similarity: float,
    current_node: Dict[str, Any],
    candidate_node: Dict[str, Any]
) -> float:
    """
    Calculate adjusted similarity score with boosts and penalties based on node attributes.
    
    Args:
        base_similarity: The base cosine similarity score.
        current_node: The current node being processed.
        candidate_node: The candidate node being considered.
        
    Returns:
        The adjusted similarity score.
    """
    if base_similarity < INITIAL_SIMILARITY_THRESHOLD:
        return base_similarity
    
    adjusted_score = base_similarity
    
    # Get node attributes
    current_theme = current_node.get('theme')
    current_cognition = current_node.get('cognition_type')
    current_emotion = current_node.get('emotion')
    
    candidate_theme = candidate_node.get('theme')
    candidate_cognition = candidate_node.get('cognition_type')
    candidate_emotion = candidate_node.get('emotion')
    
    # Apply theme match/mismatch boost/penalty
    if current_theme and candidate_theme:
        if current_theme == candidate_theme:
            adjusted_score += THEME_MATCH_BOOST
            logger.debug(f"Theme match boost: +{THEME_MATCH_BOOST}")
        else:
            adjusted_score -= THEME_MISMATCH_PENALTY
            logger.debug(f"Theme mismatch penalty: -{THEME_MISMATCH_PENALTY}")
    
    # Apply cognition type match boost only (no mismatch penalty)
    if current_cognition and candidate_cognition:
        if current_cognition == candidate_cognition:
            adjusted_score += COGNITION_MATCH_BOOST
            logger.debug(f"Cognition match boost: +{COGNITION_MATCH_BOOST}")
        # No penalty for cognition mismatch
    
    # Apply emotion match boost only (no mismatch penalty)
    if current_emotion and candidate_emotion:
        if current_emotion == candidate_emotion:
            adjusted_score += EMOTION_MATCH_BOOST
            logger.debug(f"Emotion match boost: +{EMOTION_MATCH_BOOST}")
        # No penalty for emotion mismatch
    
    # Apply temporal boost/penalty based on node timestamps
    current_timestamp = current_node.get('created_at')
    candidate_timestamp = candidate_node.get('created_at')
    
    if current_timestamp and candidate_timestamp:
        # Calculate days difference between nodes
        time_diff = abs((current_timestamp - candidate_timestamp).days)
        
        if time_diff < RECENT_DAYS_THRESHOLD:
            adjusted_score += RECENT_NODE_BOOST
            logger.debug(f"Recent node boost: +{RECENT_NODE_BOOST}")
        elif time_diff > OLDER_DAYS_THRESHOLD:
            adjusted_score -= OLDER_NODE_PENALTY
            logger.debug(f"Older node penalty: -{OLDER_NODE_PENALTY}")
    
    # For logging purposes
    logger.debug(f"Base similarity: {base_similarity:.4f}, Adjusted: {adjusted_score:.4f}")
    
    return adjusted_score