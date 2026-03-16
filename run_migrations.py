# ============================================================
# PASTE THIS FUNCTION INTO app.py (before app.run / socketio.run)
# Then call run_migrations() right after defining it
# ============================================================

import os

def run_migrations():
    database_url = os.environ.get("DATABASE_URL")

    if database_url:
        # ── PRODUCTION: PostgreSQL (Neon) ────────────────────────
        import psycopg2
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                verified INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS email_tokens (
                id SERIAL PRIMARY KEY,
                user_id INTEGER,
                token TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS businesses (
                id SERIAL PRIMARY KEY,
                user_id INTEGER UNIQUE NOT NULL,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                city TEXT NOT NULL,
                language TEXT DEFAULT 'en',
                max_clients_per_day INTEGER DEFAULT 20,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_queues (
                id SERIAL PRIMARY KEY,
                business_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(business_id, date)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS queue_entries (
                id SERIAL PRIMARY KEY,
                daily_queue_id INTEGER NOT NULL,
                client_name TEXT NOT NULL,
                client_phone TEXT,
                status TEXT DEFAULT 'waiting',
                completed_at TIMESTAMP DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                token_hash TEXT NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS booking_log (
                id SERIAL PRIMARY KEY,
                business_id INTEGER NOT NULL,
                queue_date TEXT NOT NULL,
                client_ip TEXT,
                client_phone TEXT,
                booked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()
        print("✅ PostgreSQL database ready")

    else:
        # ── LOCAL: SQLite ────────────────────────────────────────
        import sqlite3
        db_path = os.environ.get("DATABASE_PATH", "database/database.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS email_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                token TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS businesses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                city TEXT NOT NULL,
                max_clients_per_day INTEGER DEFAULT 20,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS daily_queues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (business_id) REFERENCES businesses(id),
                UNIQUE(business_id, date)
            );
            CREATE TABLE IF NOT EXISTS queue_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                daily_queue_id INTEGER NOT NULL,
                client_name TEXT NOT NULL,
                client_phone TEXT,
                status TEXT DEFAULT 'waiting',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (daily_queue_id) REFERENCES daily_queues(id)
            );
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token_hash TEXT NOT NULL,
                expires_at DATETIME NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS booking_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_id INTEGER NOT NULL,
                queue_date TEXT NOT NULL,
                client_ip TEXT,
                client_phone TEXT,
                booked_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Safe column migrations
        for sql in [
            "ALTER TABLE users ADD COLUMN verified INTEGER DEFAULT 0",
            "ALTER TABLE queue_entries ADD COLUMN completed_at TIMESTAMP DEFAULT NULL",
            "ALTER TABLE businesses ADD COLUMN language TEXT DEFAULT 'en'",
        ]:
            try:
                cursor.execute(sql)
            except Exception:
                pass

        conn.commit()
        conn.close()
        print("✅ SQLite database ready")


run_migrations()
