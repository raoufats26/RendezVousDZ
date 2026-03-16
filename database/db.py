import os
import re
from datetime import date, datetime

DATABASE_URL = os.environ.get("DATABASE_URL")  # Set on Render for production
USE_POSTGRES = bool(DATABASE_URL)

# SQLite fallback for local dev
DB_NAME = os.environ.get("DATABASE_PATH", "database/database.db")


def get_db():
    if USE_POSTGRES:
        import psycopg2
        import psycopg2.extras
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
        conn.autocommit = False
        return conn
    else:
        import sqlite3
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        return conn


def _placeholder(n=1):
    """Return the right placeholder: %s for postgres, ? for sqlite."""
    if USE_POSTGRES:
        return ','.join(['%s'] * n) if n > 1 else '%s'
    return ','.join(['?'] * n) if n > 1 else '?'


def _ph(count=1):
    """Shorthand for _placeholder."""
    return _placeholder(count)


def _execute(conn, sql, params=()):
    """
    Execute a query handling both sqlite3 and psycopg2 connections.
    For psycopg2, replaces ? with %s in SQL.
    Returns the cursor.
    """
    if USE_POSTGRES:
        sql = sql.replace('?', '%s')
        # Replace SQLite date functions with PostgreSQL equivalents
        sql = sql.replace("date('now')", "CURRENT_DATE")
        sql = sql.replace("date('now', '-6 days')", "(CURRENT_DATE - INTERVAL '6 days')")
        sql = sql.replace("date('now', '-27 days')", "(CURRENT_DATE - INTERVAL '27 days')")
        sql = sql.replace("date('now', '-29 days')", "(CURRENT_DATE - INTERVAL '29 days')")
        sql = sql.replace("strftime('%W', dq.date)", "TO_CHAR(dq.date::date, 'IW')")
        sql = sql.replace("strftime('%w', dq.date)", "EXTRACT(DOW FROM dq.date::date)::TEXT")
        sql = sql.replace("strftime('%H', qe.created_at)", "EXTRACT(HOUR FROM qe.created_at)::INTEGER::TEXT")
        sql = sql.replace("strftime('%s', 'now')", "EXTRACT(EPOCH FROM NOW())::INTEGER")
        sql = sql.replace("strftime('%s', created_at)", "EXTRACT(EPOCH FROM created_at)::INTEGER")
        cursor = conn.cursor()
        cursor.execute(sql, params)
        return cursor
    else:
        return conn.execute(sql, params)


def get_business_by_user(user_id):
    """Get business for a specific user"""
    conn = get_db()
    row = _execute(conn, "SELECT * FROM businesses WHERE user_id = ?", (user_id,)).fetchone()
    if USE_POSTGRES:
        conn.close()
        return dict(row) if row else None
    conn.close()
    return row


def get_business_by_id(business_id):
    """Get business by ID (for public booking page)"""
    conn = get_db()
    row = _execute(conn, "SELECT * FROM businesses WHERE id = ?", (business_id,)).fetchone()
    if USE_POSTGRES:
        conn.close()
        return dict(row) if row else None
    conn.close()
    return row


def create_business(user_id, name, category, city, max_clients):
    """Create a new business for a user"""
    conn = get_db()
    _execute(conn,
        "INSERT INTO businesses (user_id, name, category, city, max_clients_per_day) VALUES (?, ?, ?, ?, ?)",
        (user_id, name, category, city, max_clients)
    )
    conn.commit()
    conn.close()


def update_business(business_id, name, category, city, max_clients):
    conn = get_db()
    _execute(conn,
        "UPDATE businesses SET name = ?, category = ?, city = ?, max_clients_per_day = ? WHERE id = ?",
        (name, category, city, max_clients, business_id)
    )
    conn.commit()
    conn.close()


def get_today_queue(business_id):
    today = date.today().isoformat()
    conn = get_db()
    row = _execute(conn,
        "SELECT * FROM daily_queues WHERE business_id = ? AND date = ?",
        (business_id, today)
    ).fetchone()
    if USE_POSTGRES:
        conn.close()
        return dict(row) if row else None
    conn.close()
    return row


def create_today_queue(business_id):
    today = date.today().isoformat()
    conn = get_db()
    try:
        _execute(conn,
            "INSERT INTO daily_queues (business_id, date) VALUES (?, ?)",
            (business_id, today)
        )
        conn.commit()
    except Exception:
        if USE_POSTGRES:
            conn.rollback()
    conn.close()


def count_entries_for_queue(daily_queue_id):
    conn = get_db()
    row = _execute(conn,
        "SELECT COUNT(*) as count FROM queue_entries WHERE daily_queue_id = ?",
        (daily_queue_id,)
    ).fetchone()
    conn.close()
    return row["count"] if row else 0


def is_queue_full(daily_queue_id, max_clients):
    return count_entries_for_queue(daily_queue_id) >= max_clients


def check_duplicate_phone(daily_queue_id, client_phone):
    if not client_phone or not client_phone.strip():
        return False
    conn = get_db()
    row = _execute(conn,
        "SELECT id FROM queue_entries WHERE daily_queue_id = ? AND client_phone = ?",
        (daily_queue_id, client_phone.strip())
    ).fetchone()
    conn.close()
    return row is not None


def validate_client_name(name):
    if not name or not name.strip():
        return False, "Name is required"
    name = name.strip()
    if len(name) < 2:
        return False, "Name must be at least 2 characters"
    if len(name) > 100:
        return False, "Name is too long (maximum 100 characters)"
    if not any(c.isalpha() for c in name):
        return False, "Name must contain at least one letter"
    return True, None


def validate_phone_number(phone):
    if not phone or not phone.strip():
        return False, "Phone number is required"
    phone = phone.strip()
    phone_digits = re.sub(r'[\s\-\(\)]', '', phone)
    if not re.match(r'^\+?\d+$', phone_digits):
        return False, "Phone number can only contain digits"
    phone_digits = phone_digits.lstrip('+')
    if len(phone_digits) < 9:
        return False, "Phone number is too short"
    if len(phone_digits) > 15:
        return False, "Phone number is too long"
    return True, None


def add_queue_entry(daily_queue_id, client_name, client_phone=None):
    name_valid, name_error = validate_client_name(client_name)
    if not name_valid:
        return False, name_error

    if client_phone:
        phone_valid, phone_error = validate_phone_number(client_phone)
        if not phone_valid:
            return False, phone_error
        if check_duplicate_phone(daily_queue_id, client_phone):
            return False, "This phone number is already in today's queue"

    conn = get_db()
    try:
        _execute(conn,
            "INSERT INTO queue_entries (daily_queue_id, client_name, client_phone, status) VALUES (?, ?, ?, 'waiting')",
            (daily_queue_id, client_name.strip(), client_phone.strip() if client_phone else None)
        )
        conn.commit()
        conn.close()
        return True, "Client added to queue"
    except Exception as e:
        if USE_POSTGRES:
            conn.rollback()
        conn.close()
        return False, f"Error adding to queue: {str(e)}"


def get_queue_entries(daily_queue_id):
    conn = get_db()
    rows = _execute(conn,
        "SELECT * FROM queue_entries WHERE daily_queue_id = ? ORDER BY created_at ASC",
        (daily_queue_id,)
    ).fetchall()
    if USE_POSTGRES:
        conn.close()
        return [dict(r) for r in rows]
    conn.close()
    return rows


# ============================================================
# PHASE 15: ESTIMATED WAIT TIME FUNCTIONS
# ============================================================

def get_average_service_time(business_id, sample_size=20):
    conn = get_db()
    completed_entries = _execute(conn, """
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

    if USE_POSTGRES:
        completed_entries = [dict(r) for r in completed_entries]

    if len(completed_entries) < 2:
        return 15

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
                t_prev = timestamps[i - 1]
                t_curr = timestamps[i]
                if isinstance(t_prev, str):
                    t_prev = datetime.fromisoformat(t_prev)
                if isinstance(t_curr, str):
                    t_curr = datetime.fromisoformat(t_curr)
                gap_minutes = (t_curr - t_prev).total_seconds() / 60.0
                if 1.0 <= gap_minutes <= 120.0:
                    gaps.append(gap_minutes)
            except Exception:
                continue

    if not gaps:
        return 15

    avg_gap = sum(gaps) / len(gaps)
    return max(1, int(round(avg_gap)))


def estimate_wait_time(daily_queue_id, position, business_id):
    avg_service_time = get_average_service_time(business_id)
    people_ahead = position - 1
    if people_ahead <= 0:
        return 0
    return people_ahead * avg_service_time


def mark_entry_completed(entry_id):
    conn = get_db()
    try:
        current_time = datetime.now().isoformat()
        _execute(conn, """
            UPDATE queue_entries
            SET status = 'completed', completed_at = ?
            WHERE id = ?
        """, (current_time, entry_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        if USE_POSTGRES:
            conn.rollback()
        conn.close()
        print(f"Error marking entry as completed: {e}")
        return False


def get_queue_position(daily_queue_id, entry_id):
    conn = get_db()
    waiting_entries = _execute(conn, """
        SELECT id
        FROM queue_entries
        WHERE daily_queue_id = ? AND status = 'waiting'
        ORDER BY created_at ASC
    """, (daily_queue_id,)).fetchall()
    conn.close()

    for index, entry in enumerate(waiting_entries):
        if entry['id'] == entry_id:
            return index + 1
    return None


# ============================================================
# PHASE 18: ANTI-SPAM & SMART PROTECTION
# ============================================================

BOOKING_COOLDOWN_MINUTES = 30
NOSHOW_TIMEOUT_MINUTES   = 45


def log_booking(business_id, queue_date, client_ip, client_phone):
    conn = get_db()
    try:
        _execute(conn,
            "INSERT INTO booking_log (business_id, queue_date, client_ip, client_phone) VALUES (?, ?, ?, ?)",
            (business_id, queue_date, client_ip, client_phone)
        )
        conn.commit()
    except Exception as e:
        print(f"[booking_log] Warning: could not log booking — {e}")
        if USE_POSTGRES:
            conn.rollback()
    finally:
        conn.close()


def check_ip_cooldown(business_id, queue_date, client_ip, cooldown_minutes=None):
    if not client_ip:
        return False, 0

    minutes = cooldown_minutes if cooldown_minutes is not None else BOOKING_COOLDOWN_MINUTES
    conn = get_db()
    try:
        row = _execute(conn, """
            SELECT booked_at FROM booking_log
            WHERE business_id = ?
              AND queue_date   = ?
              AND client_ip    = ?
            ORDER BY booked_at DESC
            LIMIT 1
        """, (business_id, queue_date, client_ip)).fetchone()
    except Exception:
        conn.close()
        return False, 0
    finally:
        conn.close()

    if not row:
        return False, 0

    try:
        last_booked = row["booked_at"]
        if isinstance(last_booked, str):
            last_booked = datetime.fromisoformat(last_booked)
        elapsed = (datetime.utcnow() - last_booked.replace(tzinfo=None)).total_seconds() / 60.0
        if elapsed < minutes:
            remaining = int(minutes - elapsed) + 1
            return True, remaining
    except Exception:
        pass

    return False, 0


def cancel_noshow_entries(business_id, timeout_minutes=None):
    minutes = timeout_minutes if timeout_minutes is not None else NOSHOW_TIMEOUT_MINUTES
    conn = get_db()
    try:
        if USE_POSTGRES:
            result = _execute(conn, """
                UPDATE queue_entries
                SET status = 'skipped'
                WHERE status = 'waiting'
                  AND daily_queue_id IN (
                      SELECT id FROM daily_queues
                      WHERE business_id = ? AND date = CURRENT_DATE
                  )
                  AND EXTRACT(EPOCH FROM (NOW() - created_at)) / 60 > ?
            """, (business_id, minutes))
            cancelled = result.rowcount
        else:
            result = _execute(conn, """
                UPDATE queue_entries
                SET status = 'skipped'
                WHERE status = 'waiting'
                  AND daily_queue_id IN (
                      SELECT id FROM daily_queues
                      WHERE business_id = ? AND date = date('now')
                  )
                  AND (strftime('%s', 'now') - strftime('%s', created_at)) / 60 > ?
            """, (business_id, minutes))
            cancelled = result.rowcount
        conn.commit()
        return cancelled
    except Exception as e:
        print(f"[cancel_noshow] Warning: {e}")
        if USE_POSTGRES:
            conn.rollback()
        return 0
    finally:
        conn.close()


def check_daily_ip_limit(business_id, queue_date, client_ip, max_per_day=2):
    if not client_ip:
        return False
    conn = get_db()
    try:
        row = _execute(conn, """
            SELECT COUNT(*) as cnt FROM booking_log
            WHERE business_id = ?
              AND queue_date   = ?
              AND client_ip    = ?
        """, (business_id, queue_date, client_ip)).fetchone()
        return (row["cnt"] if row else 0) >= max_per_day
    except Exception:
        return False
    finally:
        conn.close()
