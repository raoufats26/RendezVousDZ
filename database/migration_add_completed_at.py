"""
Migration: Add completed_at column to queue_entries table
Purpose: Track completion time to calculate average service duration
Safe: Adds nullable column, does not affect existing data
"""

import sqlite3
from datetime import datetime

DB_NAME = "database/database.db"

def migrate():
    """Add completed_at column to queue_entries table"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(queue_entries)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'completed_at' in columns:
            print("✅ Column 'completed_at' already exists. Skipping migration.")
            conn.close()
            return
        
        # Add completed_at column (nullable, default NULL)
        print("📊 Adding 'completed_at' column to queue_entries table...")
        cursor.execute("""
            ALTER TABLE queue_entries 
            ADD COLUMN completed_at TIMESTAMP DEFAULT NULL
        """)
        
        conn.commit()
        print("✅ Migration completed successfully!")
        print("📝 Note: Existing entries have NULL for completed_at (expected)")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 50)
    print("MIGRATION: Add completed_at to queue_entries")
    print("=" * 50)
    migrate()
    print("=" * 50)
