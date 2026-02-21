"""
Migration: Add language column to businesses table.
Safe: adds nullable column with default 'en'.
Run once: python migration_add_language.py
"""
import sqlite3

DB_NAME = "database/database.db"

def migrate():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA table_info(businesses)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'language' in columns:
            print("✅ Column 'language' already exists. Skipping.")
            conn.close()
            return
        print("📊 Adding 'language' column to businesses table...")
        cursor.execute("ALTER TABLE businesses ADD COLUMN language TEXT DEFAULT 'en'")
        conn.commit()
        print("✅ Migration complete!")
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 50)
    print("MIGRATION: Add language to businesses")
    print("=" * 50)
    migrate()
    print("=" * 50)
