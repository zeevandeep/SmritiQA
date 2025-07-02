"""
Test for the batch_process_edges.py script.

This will process a specific number of batches for our test user.
"""
import logging
from batch_process_edges import process_all_edges

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test user ID (the one we consolidated all records to)
TEST_USER_ID = "2dfe466d-ed08-447c-9d0b-2c9eaaaef650"

def main():
    """Run a test batch process."""
    logger.info("Starting test batch processing")
    
    # Process up to 3 batches of 5 nodes each
    # This will process up to 15 nodes and create edges between them
    process_all_edges(
        user_id=TEST_USER_ID,
        batch_size=5,
        max_batches=3
    )
    
    logger.info("Test completed")

if __name__ == "__main__":
    main()