"""
Simple test script to verify the updated Node schema.

This script directly connects to the database and checks that:
1. The Node table no longer has belief_value and contradiction_flag fields
2. OpenAI prompt structure has been updated
"""
import os
import sys
import json
import logging
from sqlalchemy import inspect, create_engine
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    logger.error("DATABASE_URL environment variable not set")
    sys.exit(1)

# Import the OpenAI utils to check prompt changes
try:
    from app.utils.openai_utils import extract_nodes_from_transcript
except ImportError:
    logger.error("Failed to import extract_nodes_from_transcript")
    extract_nodes_from_transcript = None

def check_database_schema():
    """Verify the database schema reflects our changes."""
    try:
        # Connect to the database
        engine = create_engine(DATABASE_URL)
        inspector = inspect(engine)
        
        # Check if nodes table exists
        if "nodes" not in inspector.get_table_names():
            logger.error("nodes table not found in database")
            return False
        
        # Get column names for nodes table
        columns = [col["name"] for col in inspector.get_columns("nodes")]
        logger.info(f"Node table columns: {columns}")
        
        # Check that belief_value and contradiction_flag are NOT in the columns
        has_belief_value = "belief_value" in columns
        has_contradiction_flag = "contradiction_flag" in columns
        
        if has_belief_value:
            logger.error("belief_value field still exists in Node table")
        else:
            logger.info("✓ belief_value field has been removed")
            
        if has_contradiction_flag:
            logger.error("contradiction_flag field still exists in Node table")
        else:
            logger.info("✓ contradiction_flag field has been removed")
            
        # Return success only if both fields are removed
        return not (has_belief_value or has_contradiction_flag)
        
    except Exception as e:
        logger.error(f"Error checking database schema: {e}")
        return False

def check_openai_prompt():
    """Verify the OpenAI prompt structure has been updated."""
    if not extract_nodes_from_transcript:
        logger.error("Could not import extract_nodes_from_transcript function")
        return False
    
    # Check if the function's code contains the updated prompt specification
    import inspect
    func_code = inspect.getsource(extract_nodes_from_transcript)
    
    # Check for references to standardized themes and cognition types
    has_theme_list = "Themes: [" in func_code
    has_cognition_types = "Cognition Types: [" in func_code
    
    # Check that previous field references are removed
    has_old_belief_value_ref = "belief_value: Any core belief expressed" in func_code
    has_old_contradiction_flag_ref = "contradiction_flag: true if this thought" in func_code
    
    if has_theme_list and has_cognition_types:
        logger.info("✓ Prompt now includes standardized themes and cognition types")
    else:
        logger.error("Prompt doesn't include standardized themes and cognition types")
    
    if has_old_belief_value_ref or has_old_contradiction_flag_ref:
        logger.error("Prompt still references removed fields")
        return False
    else:
        logger.info("✓ Prompt no longer references removed fields")
    
    return has_theme_list and has_cognition_types and not (has_old_belief_value_ref or has_old_contradiction_flag_ref)

def main():
    """Run tests to verify schema update implementation."""
    logger.info("=== Testing Schema Updates ===")
    
    # Check database schema
    logger.info("\nChecking database schema...")
    db_schema_ok = check_database_schema()
    
    # Check OpenAI prompt
    logger.info("\nChecking OpenAI prompt...")
    prompt_ok = check_openai_prompt()
    
    # Report results
    logger.info("\n=== Results ===")
    if db_schema_ok:
        logger.info("✓ Database schema correctly updated")
    else:
        logger.error("✗ Database schema update incomplete")
    
    if prompt_ok:
        logger.info("✓ OpenAI prompt correctly updated")
    else:
        logger.error("✗ OpenAI prompt update incomplete")
    
    # Overall result
    if db_schema_ok and prompt_ok:
        logger.info("✓ Schema update successfully implemented!")
        return 0
    else:
        logger.error("✗ Schema update implementation incomplete")
        return 1

if __name__ == "__main__":
    sys.exit(main())