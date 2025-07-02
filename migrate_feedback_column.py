"""
Script to migrate the feedback column in reflections table from boolean to integer.

This allows for more nuanced feedback:
- 1 represents thumbs up (positive)
- -1 represents thumbs down (negative)
- NULL represents no feedback yet
"""
import os
from sqlalchemy import create_engine, text

def execute_migration():
    """Execute the database migration to change the feedback column type."""
    # Connect to the database
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("DATABASE_URL environment variable not found")
        return
    
    engine = create_engine(db_url)
    
    with engine.connect() as conn:
        # Begin a transaction
        with conn.begin():
            # First create a temporary column to preserve existing data
            conn.execute(text("""
                ALTER TABLE reflections 
                ADD COLUMN feedback_int INTEGER;
            """))
            
            # Convert existing boolean values to integers
            conn.execute(text("""
                UPDATE reflections 
                SET feedback_int = 
                    CASE 
                        WHEN feedback IS TRUE THEN 1
                        WHEN feedback IS FALSE THEN -1
                        ELSE NULL
                    END;
            """))
            
            # Drop the old column
            conn.execute(text("""
                ALTER TABLE reflections 
                DROP COLUMN feedback;
            """))
            
            # Rename the new column to feedback
            conn.execute(text("""
                ALTER TABLE reflections 
                RENAME COLUMN feedback_int TO feedback;
            """))
            
            print("Migration completed successfully!")

if __name__ == "__main__":
    execute_migration()