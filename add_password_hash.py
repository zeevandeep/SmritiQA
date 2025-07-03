"""
Script to add password_hash column to the users table.
"""
from sqlalchemy import Column, String, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import psycopg2
from urllib.parse import urlparse
import os

def execute_migration():
    """Execute the database migration to add the password_hash column."""
    database_url = os.environ.get("DATABASE_URL")
    
    if not database_url:
        print("DATABASE_URL environment variable not set")
        return False
    
    # Parse database URL
    url = urlparse(database_url)
    dbname = url.path[1:]
    user = url.username
    password = url.password
    host = url.hostname
    port = url.port
    
    try:
        # Connect directly using psycopg2
        conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        # Check if column exists
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='users' AND column_name='password_hash'")
        if not cur.fetchone():
            # Add column if it doesn't exist
            cur.execute("ALTER TABLE users ADD COLUMN password_hash VARCHAR(256)")
            print("Migration successful: Added password_hash column to users table")
        else:
            print("Column password_hash already exists in users table")
        
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Migration failed: {e}")
        return False

if __name__ == "__main__":
    execute_migration()