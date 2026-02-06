from flask import Blueprint, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import get_db
import re
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import current_app
import secrets


limiter = Limiter(get_remote_address, app=current_app)

auth_bp = Blueprint("auth", __name__)

# ---------------------------
# HELPERS
# ---------------------------

def valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def password_strong(password):
    return len(password) >= 8

# ---------------------------
# REGISTER
# ---------------------------

@auth_bp.route("/register", methods=["GET","POST"])
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
                "SELECT id FROM users WHERE email=?",
                (email,)
            ).fetchone()

            if existing:
                error = "Email already registered"
            else:
                db.execute(
                    "INSERT INTO users (email,password_hash,verified) VALUES (?,?,0)",
                    (email, generate_password_hash(password))
                )
                user_id = db.execute(
                    "SELECT id FROM users WHERE email=?",
                    (email,)
                ).fetchone()["id"]

                token = secrets.token_urlsafe(32)

                db.execute(
                    "INSERT INTO email_tokens (user_id,token) VALUES (?,?)",
                    (user_id, token)
                )
                db.commit()

                print("VERIFY LINK:")
                print(f"http://127.0.0.1:5000/verify/{token}")

                return "Check console for verification link (email sending later)"

    return render_template("register.html", error=error)


# ---------------------------
# LOGIN
# ---------------------------

@auth_bp.route("/login", methods=["GET","POST"])
@limiter.limit("5 per minute")
def login():
    error = None

    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
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

@auth_bp.route("/verify/<token>")
def verify_email(token):
    db = get_db()

    row = db.execute(
        "SELECT user_id FROM email_tokens WHERE token=?",
        (token,)
    ).fetchone()

    if not row:
        return "Invalid or expired token"

    db.execute(
        "UPDATE users SET verified=1 WHERE id=?",
        (row["user_id"],)
    )

    db.execute(
        "DELETE FROM email_tokens WHERE token=?",
        (token,)
    )

    db.commit()

    return "Email verified. You can now login."

