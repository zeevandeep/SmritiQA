"""
Add profile_image_url column to user_profiles table for Google OAuth integration.
"""
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def execute_migration():
    """Add the profile_image_url column to the user_profiles table."""
    try:
        # Get database URL from environment
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL environment variable not found")
        
        # Connect to the database
        conn = psycopg2.connect(database_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'user_profiles' 
            AND column_name = 'profile_image_url'
        """)
        
        if cursor.fetchone():
            print("Column 'profile_image_url' already exists in user_profiles table")
            return
        
        # Add the profile_image_url column
        print("Adding profile_image_url column to user_profiles table...")
        cursor.execute("""
            ALTER TABLE user_profiles 
            ADD COLUMN profile_image_url TEXT
        """)
        
        print("✅ Successfully added profile_image_url column to user_profiles table")
        
    except Exception as e:
        print(f"❌ Error adding profile_image_url column: {e}")
        raise
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    execute_migration()