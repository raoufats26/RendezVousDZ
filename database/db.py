import sqlite3

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

def create_business(user_id, name, category, city, max_clients):
    """Create a new business for a user"""
    conn = get_db()
    conn.execute(
        "INSERT INTO businesses (user_id, name, category, city, max_clients_per_day) VALUES (?, ?, ?, ?, ?)",
        (user_id, name, category, city, max_clients)
    )
    conn.commit()
    conn.close()