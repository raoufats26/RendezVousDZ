"""
Migration: Phase 18 — Anti-Spam & Smart Protection
Adds:
  - booking_log: tracks IP + phone + timestamp for cooldown/duplicate IP protection
  - queue_entries.expires_at: for auto-cancel no-show logic

Run once: python migration_phase18.py
"""

import sqlite3

DB_NAME = "database/database.db"

def migrate():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        # ── 1. booking_log table ─────────────────────────────────────────────
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS booking_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                business_id INTEGER NOT NULL,
                queue_date  TEXT    NOT NULL,
                client_ip   TEXT,
                client_phone TEXT,
                booked_at   DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Table 'booking_log' ready.")

        # ── 2. Add expires_at to queue_entries (nullable) ────────────────────
        cursor.execute("PRAGMA table_info(queue_entries)")
        cols = [c[1] for c in cursor.fetchall()]

        if 'expires_at' not in cols:
            cursor.execute("""
                ALTER TABLE queue_entries
                ADD COLUMN expires_at DATETIME DEFAULT NULL
            """)
            print("✅ Column 'expires_at' added to queue_entries.")
        else:
            print("✅ Column 'expires_at' already exists. Skipping.")

        conn.commit()
        print("✅ Phase 18 migration complete!")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    print("=" * 50)
    print("MIGRATION: Phase 18 — Anti-Spam Protection")
    print("=" * 50)
    migrate()
    print("=" * 50)
