import sqlite3
from datetime import date, datetime
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

def update_business(business_id, name, category, city, max_clients):
    """
    Update business settings.
    Does NOT affect existing queue entries.
    New max_clients applies to future queues only.
    """
    conn = get_db()
    conn.execute(
        "UPDATE businesses SET name = ?, category = ?, city = ?, max_clients_per_day = ? WHERE id = ?",
        (name, category, city, max_clients, business_id)
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

# ========================================
# PHASE 15: ESTIMATED WAIT TIME FUNCTIONS
# ========================================

def get_average_service_time(business_id, sample_size=10):
    """
    Calculate average service time in minutes based on recent completed entries.
    
    Args:
        business_id: The business ID
        sample_size: Number of recent completed entries to analyze (default: 10)
    
    Returns:
        Average service time in minutes (integer), or 15 if insufficient data
    """
    conn = get_db()
    
    # Get last N completed entries with both created_at and completed_at
    completed_entries = conn.execute("""
        SELECT 
            qe.created_at,
            qe.completed_at
        FROM queue_entries qe
        JOIN daily_queues dq ON qe.daily_queue_id = dq.id
        WHERE dq.business_id = ?
            AND qe.status = 'completed'
            AND qe.completed_at IS NOT NULL
        ORDER BY qe.completed_at DESC
        LIMIT ?
    """, (business_id, sample_size)).fetchall()
    
    conn.close()
    
    # If we don't have enough data, return default
    if len(completed_entries) < 3:
        return 15  # Default: 15 minutes
    
    # Calculate service durations
    durations = []
    for entry in completed_entries:
        try:
            created = datetime.fromisoformat(entry['created_at'])
            completed = datetime.fromisoformat(entry['completed_at'])
            duration_minutes = (completed - created).total_seconds() / 60
            
            # Sanity check: ignore unrealistic durations
            if 1 <= duration_minutes <= 180:  # Between 1 minute and 3 hours
                durations.append(duration_minutes)
        except:
            continue
    
    # If no valid durations found, return default
    if not durations:
        return 15
    
    # Calculate average and round to nearest minute
    avg_duration = sum(durations) / len(durations)
    return max(5, int(round(avg_duration)))  # Minimum 5 minutes


def estimate_wait_time(daily_queue_id, position, business_id):
    """
    Estimate wait time for a client at a given position in the queue.
    
    Args:
        daily_queue_id: The daily queue ID
        position: Client's position in queue (1-based, so position 1 = first in line)
        business_id: The business ID (for calculating avg service time)
    
    Returns:
        Estimated wait time in minutes (integer)
    """
    # Get average service time
    avg_service_time = get_average_service_time(business_id)
    
    # Calculate wait time
    # Position 1 means "you're next" = 1 person ahead
    # Position 2 means 2 people ahead, etc.
    people_ahead = position - 1
    
    if people_ahead <= 0:
        return 0  # You're being served or first in line
    
    estimated_minutes = people_ahead * avg_service_time
    
    return estimated_minutes


def mark_entry_completed(entry_id):
    """
    Mark a queue entry as completed and record completion timestamp.
    
    Args:
        entry_id: The queue entry ID
    
    Returns:
        True if successful, False otherwise
    """
    conn = get_db()
    
    try:
        current_time = datetime.now().isoformat()
        
        conn.execute("""
            UPDATE queue_entries 
            SET status = 'completed', completed_at = ? 
            WHERE id = ?
        """, (current_time, entry_id))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.close()
        print(f"Error marking entry as completed: {e}")
        return False


def get_queue_position(daily_queue_id, entry_id):
    """
    Get the position of a specific entry in the queue (1-based).
    Only counts 'waiting' entries.
    
    Args:
        daily_queue_id: The daily queue ID
        entry_id: The specific entry ID
    
    Returns:
        Position number (1-based), or None if not found
    """
    conn = get_db()
    
    # Get all waiting entries ordered by creation time
    waiting_entries = conn.execute("""
        SELECT id 
        FROM queue_entries 
        WHERE daily_queue_id = ? AND status = 'waiting'
        ORDER BY created_at ASC
    """, (daily_queue_id,)).fetchall()
    
    conn.close()
    
    # Find position
    for index, entry in enumerate(waiting_entries):
        if entry['id'] == entry_id:
            return index + 1  # 1-based position
    
    return None
