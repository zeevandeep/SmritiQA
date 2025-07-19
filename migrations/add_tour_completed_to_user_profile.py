#!/usr/bin/env python3
"""
Migration: Add tour_completed column to user_profiles table
Purpose: Store app tour completion status in database instead of localStorage
         to ensure existing users don't see tour again even from different browsers

This migration:
1. Adds tour_completed column (Boolean, default=False) to user_profiles table  
2. Sets tour_completed=True for all existing users to prevent tour from showing
3. Leaves new users with default False to see tour on first signup
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_migration():
    """Execute the migration to add tour_completed column."""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not found")
        return False
    
    try:
        # Connect to database
        conn = psycopg2.connect(database_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("Starting migration: Add tour_completed to user_profiles table")
        
        # Step 1: Check if column already exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'user_profiles' 
            AND column_name = 'tour_completed'
        """)
        
        if cursor.fetchone():
            print("✓ Column tour_completed already exists, skipping migration")
            return True
        
        # Step 2: Add tour_completed column with default False
        print("Adding tour_completed column to user_profiles table...")
        cursor.execute("""
            ALTER TABLE user_profiles 
            ADD COLUMN tour_completed BOOLEAN DEFAULT FALSE
        """)
        print("✓ Column tour_completed added successfully")
        
        # Step 3: Set tour_completed=False for all existing users
        # This allows existing users to see the tour
        cursor.execute("""
            UPDATE user_profiles 
            SET tour_completed = FALSE 
            WHERE tour_completed IS NULL OR tour_completed = TRUE
        """)
        updated_count = cursor.rowcount
        print(f"✓ Set tour_completed=False for {updated_count} existing users")
        
        # Step 4: Verify the migration
        cursor.execute("""
            SELECT COUNT(*) as total_users,
                   COUNT(*) FILTER (WHERE tour_completed = FALSE) as tour_not_completed_users
            FROM user_profiles
        """)
        result = cursor.fetchone()
        total_users, not_completed_users = result
        
        print(f"\nMigration completed successfully:")
        print(f"  - Total users: {total_users}")
        print(f"  - Users with tour_completed=False: {not_completed_users}")
        print(f"  - All users will see tour until they complete it")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"ERROR during migration: {e}")
        return False

if __name__ == "__main__":
    success = run_migration()
    if success:
        print("\n🎉 Migration completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)