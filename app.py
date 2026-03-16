import eventlet
eventlet.monkey_patch()

import os
from flask import Flask, render_template
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO, emit, join_room, leave_room

from routes.auth import auth_bp
from routes.booking import booking_bp
from routes.analytics import analytics_bp
from routes.display import display_bp


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dqsjhlfqksmù*&é&é'_& ")

# ---------------------------
# FLASK-MAIL CONFIGURATION
# ---------------------------
app.config['MAIL_SERVER']         = os.environ.get('MAIL_SERVER',         'smtp.gmail.com')
app.config['MAIL_PORT']           = int(os.environ.get('MAIL_PORT',       587))
app.config['MAIL_USE_TLS']        = os.environ.get('MAIL_USE_TLS',        'true').lower() == 'true'
app.config['MAIL_USERNAME']       = os.environ.get('MAIL_USERNAME',       '')
app.config['MAIL_PASSWORD']       = os.environ.get('MAIL_PASSWORD',       '')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@rendezvousdz.com')

try:
    from flask_mail import Mail
    mail = Mail(app)
except ImportError:
    pass


# ---------------------------
# DATABASE MIGRATIONS
# ---------------------------

def run_migrations():
    database_url = os.environ.get("DATABASE_URL")

    if database_url:
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


# ---------------------------
# SOCKETIO & LIMITER
# ---------------------------

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)

# ---------------------------
# BLUEPRINTS
# ---------------------------

app.register_blueprint(auth_bp)
app.register_blueprint(booking_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(display_bp)

# Simple i18n shim
def _(s): return s
app.jinja_env.globals['_'] = _


# ---------------------------
# SOCKETIO EVENTS
# ---------------------------

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('join')
def handle_join(data):
    business_id = data.get('business_id')
    if business_id:
        room = f'business_{business_id}'
        join_room(room)
        print(f'Client joined room: {room}')
        emit('joined', {'room': room})


# ---------------------------
# ROUTES
# ---------------------------

@app.route("/")
def home():
    return render_template("home.html")


# ---------------------------
# ERROR HANDLERS
# ---------------------------

@app.errorhandler(404)
def page_not_found(e):
    return render_template("public_booking.html",
                           error="Page not found", business=None), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template("public_booking.html",
                           error="An error occurred. Please try again later.", business=None), 500

@app.errorhandler(Exception)
def handle_exception(e):
    print(f"Unexpected error: {str(e)}")
    return render_template("public_booking.html",
                           error="An unexpected error occurred. Please try again.", business=None), 500


if __name__ == "__main__":
    socketio.run(app, debug=True)
