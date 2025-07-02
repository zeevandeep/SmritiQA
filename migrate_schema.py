"""
Script to migrate the database schema by removing the belief_value and contradiction_flag columns.
"""
import os
import sys
import logging
from sqlalchemy import create_engine, text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    logger.error("DATABASE_URL environment variable not set")
    sys.exit(1)

def execute_migration():
    """Execute the schema migration to remove the columns."""
    try:
        # Connect to the database
        engine = create_engine(DATABASE_URL)
        
        # Start a transaction
        with engine.connect() as connection:
            with connection.begin():
                # Check if columns exist before dropping
                result = connection.execute(text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name = 'nodes' AND column_name IN ('belief_value', 'contradiction_flag')"
                ))
                columns_to_drop = [row[0] for row in result]
                
                if not columns_to_drop:
                    logger.info("Columns already dropped, no migration needed")
                    return True
                
                logger.info(f"Found columns to drop: {columns_to_drop}")
                
                # Build the ALTER TABLE statement
                drop_statements = []
                for column in columns_to_drop:
                    drop_statements.append(f"DROP COLUMN {column}")
                
                if drop_statements:
                    sql = f"ALTER TABLE nodes {', '.join(drop_statements)}"
                    logger.info(f"Executing: {sql}")
                    connection.execute(text(sql))
                    logger.info("Migration successful!")
                    return True
                else:
                    logger.info("No columns to drop")
                    return True
                
    except Exception as e:
        logger.error(f"Error executing migration: {e}")
        return False

if __name__ == "__main__":
    if execute_migration():
        sys.exit(0)
    else:
        sys.exit(1)