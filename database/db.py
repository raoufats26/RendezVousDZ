import sqlite3
from datetime import date

DB_NAME = "database/database.db"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def get_business_by_user(user_id):
    """Get business for a specific user"""
    conn = get_db()
    business = conn.execute(
        "SELECT * FROM businesses WHERE user_id = ?",
        (user_id,)
    ).fetchone()
    conn.close()
    return business

def get_business_by_id(business_id):
    """Get business by ID (for public booking page)"""
    conn = get_db()
    business = conn.execute(
        "SELECT * FROM businesses WHERE id = ?",
        (business_id,)
    ).fetchone()
    conn.close()
    return business

def create_business(user_id, name, category, city, max_clients):
    """Create a new business for a user"""
    conn = get_db()
    conn.execute(
        "INSERT INTO businesses (user_id, name, category, city, max_clients_per_day) VALUES (?, ?, ?, ?, ?)",
        (user_id, name, category, city, max_clients)
    )
    conn.commit()
    conn.close()

def get_today_queue(business_id):
    """Get today's queue for a business. Returns None if doesn't exist."""
    today = date.today().isoformat()  # YYYY-MM-DD format
    conn = get_db()
    queue = conn.execute(
        "SELECT * FROM daily_queues WHERE business_id = ? AND date = ?",
        (business_id, today)
    ).fetchone()
    conn.close()
    return queue

def create_today_queue(business_id):
    """Create today's queue for a business. Safe - won't duplicate."""
    today = date.today().isoformat()  # YYYY-MM-DD format
    conn = get_db()
    
    try:
        conn.execute(
            "INSERT INTO daily_queues (business_id, date) VALUES (?, ?)",
            (business_id, today)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        # Queue already exists for this business/date - this is safe
        pass
    
    conn.close()

def count_entries_for_queue(daily_queue_id):
    """Count total entries in a specific daily queue"""
    conn = get_db()
    count = conn.execute(
        "SELECT COUNT(*) as count FROM queue_entries WHERE daily_queue_id = ?",
        (daily_queue_id,)
    ).fetchone()["count"]
    conn.close()
    return count

def is_queue_full(daily_queue_id, max_clients):
    """Check if queue has reached its daily limit"""
    current_count = count_entries_for_queue(daily_queue_id)
    return current_count >= max_clients

def add_queue_entry(daily_queue_id, client_name, client_phone=None):
    """Add a client to the queue. Returns success boolean and message."""
    conn = get_db()
    
    try:
        conn.execute(
            "INSERT INTO queue_entries (daily_queue_id, client_name, client_phone, status) VALUES (?, ?, ?, 'waiting')",
            (daily_queue_id, client_name, client_phone)
        )
        conn.commit()
        conn.close()
        return True, "Client added to queue"
    except Exception as e:
        conn.close()
        return False, f"Error adding to queue: {str(e)}"

def get_queue_entries(daily_queue_id):
    """Get all entries for a specific daily queue"""
    conn = get_db()
    entries = conn.execute(
        "SELECT * FROM queue_entries WHERE daily_queue_id = ? ORDER BY created_at ASC",
        (daily_queue_id,)
    ).fetchall()
    conn.close()
    return entries