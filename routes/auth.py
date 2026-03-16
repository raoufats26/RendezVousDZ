import os
import re
import secrets
import hashlib
from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, redirect, session, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Message

from database.db import get_db, _execute, USE_POSTGRES

auth_bp = Blueprint("auth", __name__)
limiter = Limiter(get_remote_address, app=current_app)

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:5000")

# ---------------------------
# HELPERS
# ---------------------------

def valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def password_strong(password):
    return len(password) >= 8

def hash_token(token):
    return hashlib.sha256(token.encode()).hexdigest()

def send_email(subject, recipient, body_html):
    try:
        mail = current_app.extensions['mail']
        msg = Message(
            subject=subject,
            recipients=[recipient],
            html=body_html,
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        mail.send(msg)
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
        return False

def row_to_dict(row):
    if row is None:
        return None
    if isinstance(row, dict):
        return row
    return dict(row)

# ---------------------------
# REGISTER
# ---------------------------

@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def register():
    error = None

    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if not valid_email(email):
            error = "Invalid email format"
        elif not password_strong(password):
            error = "Password must be at least 8 characters"
        else:
            db = get_db()

            existing = _execute(db, "SELECT id FROM users WHERE email=?", (email,)).fetchone()

            if existing:
                error = "Email already registered"
                db.close()
            else:
                _execute(db,
                    "INSERT INTO users (email, password_hash, verified) VALUES (?, ?, 1)",
                    (email, generate_password_hash(password))
                )
                db.commit()

                user_row = _execute(db, "SELECT id FROM users WHERE email=?", (email,)).fetchone()
                user_id = user_row["id"] if isinstance(user_row, dict) else user_row[0]

                token = secrets.token_urlsafe(32)

                _execute(db,
                    "INSERT INTO email_tokens (user_id, token) VALUES (?, ?)",
                    (user_id, token)
                )
                db.commit()
                db.close()

                verify_link = f"{BASE_URL}/verify/{token}"

                sent = send_email(
                    subject="Verify your RendezVousDZ account",
                    recipient=email,
                    body_html=f"""
                        <h2>Welcome to RendezVousDZ!</h2>
                        <p>Click the link below to verify your email address:</p>
                        <p><a href="{verify_link}">{verify_link}</a></p>
                        <p>This link is valid for 24 hours.</p>
                    """
                )

                if not sent:
                    print(f"VERIFY LINK (fallback): {verify_link}")

                return render_template("register.html", success=True)

    return render_template("register.html", error=error)


# ---------------------------
# LOGIN
# ---------------------------

@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def login():
    error = None

    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        db = get_db()
        user = row_to_dict(_execute(db, "SELECT * FROM users WHERE email=?", (email,)).fetchone())
        db.close()

        if not user:
            error = "Invalid credentials"
        elif user["verified"] == 0:
            error = "Please verify your email first"
        elif not check_password_hash(user["password_hash"], password):
            error = "Invalid credentials"
        else:
            session.clear()
            session["user_id"] = user["id"]
            return redirect("/dashboard")

    return render_template("login.html", error=error)


# ---------------------------
# LOGOUT
# ---------------------------

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ---------------------------
# EMAIL VERIFICATION
# ---------------------------

@auth_bp.route("/verify/<token>")
def verify_email(token):
    db = get_db()

    row = row_to_dict(_execute(db, "SELECT user_id FROM email_tokens WHERE token=?", (token,)).fetchone())

    if not row:
        db.close()
        return "Invalid or expired token"

    _execute(db, "UPDATE users SET verified=1 WHERE id=?", (row["user_id"],))
    _execute(db, "DELETE FROM email_tokens WHERE token=?", (token,))
    db.commit()
    db.close()

    return redirect("/login")


# ---------------------------
# FORGOT PASSWORD
# ---------------------------

@auth_bp.route("/forgot-password", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()

        if valid_email(email):
            db = get_db()
            user = row_to_dict(_execute(db, "SELECT id FROM users WHERE email=?", (email,)).fetchone())

            if user:
                _execute(db,
                    "DELETE FROM password_reset_tokens WHERE user_id=?",
                    (user["id"],)
                )

                raw_token = secrets.token_urlsafe(32)
                token_hash = hash_token(raw_token)
                expires_at = (datetime.utcnow() + timedelta(hours=1)).isoformat()

                _execute(db,
                    "INSERT INTO password_reset_tokens (user_id, token_hash, expires_at) VALUES (?, ?, ?)",
                    (user["id"], token_hash, expires_at)
                )
                db.commit()
                db.close()

                reset_link = f"{BASE_URL}/reset-password/{raw_token}"

                sent = send_email(
                    subject="Reset your RendezVousDZ password",
                    recipient=email,
                    body_html=f"""
                        <h2>Password Reset Request</h2>
                        <p>Click the link below to reset your password:</p>
                        <p><a href="{reset_link}">{reset_link}</a></p>
                        <p>This link expires in <strong>1 hour</strong>.</p>
                        <p>If you did not request this, ignore this email.</p>
                    """
                )

                if not sent:
                    print(f"RESET LINK (fallback): {reset_link}")
            else:
                db.close()

        return render_template("forgot_password.html", success=True)

    return render_template("forgot_password.html")


# ---------------------------
# RESET PASSWORD
# ---------------------------

@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    token_hash = hash_token(token)
    db = get_db()

    row = row_to_dict(_execute(db,
        "SELECT * FROM password_reset_tokens WHERE token_hash=?",
        (token_hash,)
    ).fetchone())

    if not row:
        db.close()
        return render_template("reset_password.html", error="Invalid or expired reset link.")

    expires_at = row["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    else:
        expires_at = expires_at.replace(tzinfo=None)

    if datetime.utcnow() > expires_at:
        _execute(db, "DELETE FROM password_reset_tokens WHERE token_hash=?", (token_hash,))
        db.commit()
        db.close()
        return render_template("reset_password.html", error="This reset link has expired. Please request a new one.")

    if request.method == "POST":
        new_password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not password_strong(new_password):
            db.close()
            return render_template("reset_password.html", token=token, error="Password must be at least 8 characters.")

        if new_password != confirm_password:
            db.close()
            return render_template("reset_password.html", token=token, error="Passwords do not match.")

        _execute(db,
            "UPDATE users SET password_hash=? WHERE id=?",
            (generate_password_hash(new_password), row["user_id"])
        )
        _execute(db, "DELETE FROM password_reset_tokens WHERE token_hash=?", (token_hash,))
        db.commit()
        db.close()

        return render_template("reset_password.html", success=True)

    db.close()
    return render_template("reset_password.html", token=token)
