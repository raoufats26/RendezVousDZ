import re
import secrets
import hashlib
from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, redirect, session, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Message

from database.db import get_db

auth_bp = Blueprint("auth", __name__)
limiter = Limiter(get_remote_address, app=current_app)

# ---------------------------
# HELPERS
# ---------------------------

def valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def password_strong(password):
    return len(password) >= 8

def hash_token(token):
    """SHA-256 hash a token before storing it in DB."""
    return hashlib.sha256(token.encode()).hexdigest()

def send_email(subject, recipient, body_html):
    """
    Send an email using Flask-Mail.
    mail must be initialized in app.py and passed via current_app extensions.
    """
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

            existing = db.execute(
                "SELECT id FROM users WHERE email=?", (email,)
            ).fetchone()

            if existing:
                error = "Email already registered"
            else:
                db.execute(
                    "INSERT INTO users (email, password_hash, verified) VALUES (?, ?, 0)",
                    (email, generate_password_hash(password))
                )
                user_id = db.execute(
                    "SELECT id FROM users WHERE email=?", (email,)
                ).fetchone()["id"]

                token = secrets.token_urlsafe(32)

                db.execute(
                    "INSERT INTO email_tokens (user_id, token) VALUES (?, ?)",
                    (user_id, token)
                )
                db.commit()

                verify_link = f"http://127.0.0.1:5000/verify/{token}"

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
        user = db.execute(
            "SELECT * FROM users WHERE email=?", (email,)
        ).fetchone()

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

    row = db.execute(
        "SELECT user_id FROM email_tokens WHERE token=?", (token,)
    ).fetchone()

    if not row:
        return "Invalid or expired token"

    db.execute("UPDATE users SET verified=1 WHERE id=?", (row["user_id"],))
    db.execute("DELETE FROM email_tokens WHERE token=?", (token,))
    db.commit()

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
            user = db.execute(
                "SELECT id FROM users WHERE email=?", (email,)
            ).fetchone()

            if user:
                # Clean up any existing tokens for this user
                db.execute(
                    "DELETE FROM password_reset_tokens WHERE user_id=?",
                    (user["id"],)
                )

                # Generate secure token
                raw_token = secrets.token_urlsafe(32)
                token_hash = hash_token(raw_token)
                expires_at = (datetime.utcnow() + timedelta(hours=1)).isoformat()

                db.execute(
                    "INSERT INTO password_reset_tokens (user_id, token_hash, expires_at) VALUES (?, ?, ?)",
                    (user["id"], token_hash, expires_at)
                )
                db.commit()

                reset_link = f"http://127.0.0.1:5000/reset-password/{raw_token}"

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

        # Always show generic message — no user enumeration
        return render_template("forgot_password.html", success=True)

    return render_template("forgot_password.html")


# ---------------------------
# RESET PASSWORD
# ---------------------------

@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    token_hash = hash_token(token)
    db = get_db()

    row = db.execute(
        "SELECT * FROM password_reset_tokens WHERE token_hash=?",
        (token_hash,)
    ).fetchone()

    # Token not found
    if not row:
        return render_template("reset_password.html", error="Invalid or expired reset link.")

    # Check expiry
    expires_at = datetime.fromisoformat(row["expires_at"])
    if datetime.utcnow() > expires_at:
        db.execute("DELETE FROM password_reset_tokens WHERE token_hash=?", (token_hash,))
        db.commit()
        return render_template("reset_password.html", error="This reset link has expired. Please request a new one.")

    if request.method == "POST":
        new_password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not password_strong(new_password):
            return render_template("reset_password.html", token=token, error="Password must be at least 8 characters.")

        if new_password != confirm_password:
            return render_template("reset_password.html", token=token, error="Passwords do not match.")

        # Update password
        db.execute(
            "UPDATE users SET password_hash=? WHERE id=?",
            (generate_password_hash(new_password), row["user_id"])
        )

        # Invalidate token
        db.execute("DELETE FROM password_reset_tokens WHERE token_hash=?", (token_hash,))
        db.commit()

        return render_template("reset_password.html", success=True)

    return render_template("reset_password.html", token=token)