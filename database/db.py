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


# ============================================================
# PHASE 15: ESTIMATED WAIT TIME FUNCTIONS
# ============================================================

def get_average_service_time(business_id, sample_size=20):
    """
    Calculate average service time in minutes.

    METHOD: Use the gap between consecutive completed_at timestamps
    within the same daily queue, ordered by completion time.
    This measures how long it takes to serve one person after the
    previous one was done — which is the true "service duration".

    Fallback: if not enough data, return 15 min default.

    Args:
        business_id: The business ID
        sample_size: Number of recent completed entries to pull (default 20)

    Returns:
        Average service time in minutes (integer), minimum 1.
    """
    conn = get_db()

    # Fetch recent completed entries grouped by queue, ordered by completion time.
    # We need at least 2 completions in the same queue to compute a gap.
    completed_entries = conn.execute("""
        SELECT
            qe.completed_at,
            dq.id AS queue_id
        FROM queue_entries qe
        JOIN daily_queues dq ON qe.daily_queue_id = dq.id
        WHERE dq.business_id = ?
          AND qe.status = 'completed'
          AND qe.completed_at IS NOT NULL
        ORDER BY dq.id ASC, qe.completed_at ASC
        LIMIT ?
    """, (business_id, sample_size)).fetchall()

    conn.close()

    if len(completed_entries) < 2:
        return 15  # Default: 15 minutes

    # Group by queue_id, then compute consecutive gaps within each queue
    from collections import defaultdict
    by_queue = defaultdict(list)
    for row in completed_entries:
        by_queue[row['queue_id']].append(row['completed_at'])

    gaps = []
    for queue_id, timestamps in by_queue.items():
        if len(timestamps) < 2:
            continue
        for i in range(1, len(timestamps)):
            try:
                t_prev = datetime.fromisoformat(timestamps[i - 1])
                t_curr = datetime.fromisoformat(timestamps[i])
                gap_minutes = (t_curr - t_prev).total_seconds() / 60.0

                # Sanity check: service gap must be between 1 min and 2 hours
                # Gaps > 120 min likely mean idle time between customers, not service time
                if 1.0 <= gap_minutes <= 120.0:
                    gaps.append(gap_minutes)
            except Exception:
                continue

    if not gaps:
        # No valid gaps found — fall back to created_at → completed_at
        # but only if the durations are plausible (capped at 60 min)
        conn2 = get_db()
        fallback_rows = conn2.execute("""
            SELECT qe.created_at, qe.completed_at
            FROM queue_entries qe
            JOIN daily_queues dq ON qe.daily_queue_id = dq.id
            WHERE dq.business_id = ?
              AND qe.status = 'completed'
              AND qe.completed_at IS NOT NULL
            ORDER BY qe.completed_at DESC
            LIMIT ?
        """, (business_id, sample_size)).fetchall()
        conn2.close()

        durations = []
        for row in fallback_rows:
            try:
                created   = datetime.fromisoformat(row['created_at'])
                completed = datetime.fromisoformat(row['completed_at'])
                dur = (completed - created).total_seconds() / 60.0
                # For the fallback keep it tight: 1–45 min is credible service time
                if 1.0 <= dur <= 45.0:
                    durations.append(dur)
            except Exception:
                continue

        if not durations:
            return 15

        avg = sum(durations) / len(durations)
        return max(1, int(round(avg)))

    avg_gap = sum(gaps) / len(gaps)
    return max(1, int(round(avg_gap)))


def estimate_wait_time(daily_queue_id, position, business_id):
    """
    Estimate wait time for a client at a given position in the queue.

    Args:
        daily_queue_id: The daily queue ID
        position: Client's position in queue (1-based: position 1 = first)
        business_id: The business ID

    Returns:
        Estimated wait time in minutes (integer)
    """
    avg_service_time = get_average_service_time(business_id)

    # People ahead = position - 1
    # Position 1 means you ARE first (no one ahead) → 0 wait
    people_ahead = position - 1

    if people_ahead <= 0:
        return 0

    return people_ahead * avg_service_time


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
