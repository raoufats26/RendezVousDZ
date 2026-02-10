import sqlite3
from datetime import date
import re

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

def check_duplicate_phone(daily_queue_id, client_phone):
    """
    Check if phone number already exists in today's queue.
    Returns True if duplicate found, False otherwise.
    """
    if not client_phone or not client_phone.strip():
        return False
    
    conn = get_db()
    existing = conn.execute(
        "SELECT id FROM queue_entries WHERE daily_queue_id = ? AND client_phone = ?",
        (daily_queue_id, client_phone.strip())
    ).fetchone()
    conn.close()
    
    return existing is not None

def validate_client_name(name):
    """
    Validate client name.
    Returns (is_valid, error_message)
    """
    if not name or not name.strip():
        return False, "Name is required"
    
    name = name.strip()
    
    if len(name) < 2:
        return False, "Name must be at least 2 characters"
    
    if len(name) > 100:
        return False, "Name is too long (maximum 100 characters)"
    
    # Check if name contains at least one letter
    if not any(c.isalpha() for c in name):
        return False, "Name must contain at least one letter"
    
    return True, None

def validate_phone_number(phone):
    """
    Validate phone number (basic Algerian format).
    Returns (is_valid, error_message)
    """
    if not phone or not phone.strip():
        return False, "Phone number is required"
    
    phone = phone.strip()
    
    # Remove common separators for validation
    phone_digits = re.sub(r'[\s\-\(\)]', '', phone)
    
    # Check if contains only digits (and optional + at start)
    if not re.match(r'^\+?\d+$', phone_digits):
        return False, "Phone number can only contain digits"
    
    # Remove + for length check
    phone_digits = phone_digits.lstrip('+')
    
    # Algerian numbers are typically 10 digits (05xxxxxxxx) or 9 digits
    if len(phone_digits) < 9:
        return False, "Phone number is too short"
    
    if len(phone_digits) > 15:
        return False, "Phone number is too long"
    
    return True, None

def add_queue_entry(daily_queue_id, client_name, client_phone=None):
    """Add a client to the queue. Returns success boolean and message."""
    
    # Validate name
    name_valid, name_error = validate_client_name(client_name)
    if not name_valid:
        return False, name_error
    
    # Validate phone if provided
    if client_phone:
        phone_valid, phone_error = validate_phone_number(client_phone)
        if not phone_valid:
            return False, phone_error
        
        # Check for duplicate phone number
        if check_duplicate_phone(daily_queue_id, client_phone):
            return False, "This phone number is already in today's queue"
    
    conn = get_db()
    
    try:
        conn.execute(
            "INSERT INTO queue_entries (daily_queue_id, client_name, client_phone, status) VALUES (?, ?, ?, 'waiting')",
            (daily_queue_id, client_name.strip(), client_phone.strip() if client_phone else None)
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
