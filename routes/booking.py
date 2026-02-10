from flask import Blueprint, render_template, request, redirect, session
from database.db import get_db, get_business_by_user, create_business

booking_bp = Blueprint("booking", __name__)

MAX_CLIENTS = 20

@booking_bp.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]
    
    # Check if user has a business
    business = get_business_by_user(user_id)
    
    if not business:
        # User has no business - show create form
        return render_template("create_business.html")
    
    # User has business - show dashboard with queue
    db = get_db()
    queue = db.execute(
        "SELECT * FROM queue_entries ORDER BY queue_number"
    ).fetchall()

    return render_template("dashboard.html", queue=queue, business=business)

@booking_bp.route("/create-business", methods=["POST"])
def create_business_route():
    if "user_id" not in session:
        return redirect("/login")
    
    user_id = session["user_id"]
    
    # Check if user already has a business
    existing = get_business_by_user(user_id)
    if existing:
        return redirect("/dashboard")
    
    # Get form data
    name = request.form.get("name", "").strip()
    category = request.form.get("category", "").strip()
    city = request.form.get("city", "").strip()
    max_clients = request.form.get("max_clients", 20)
    
    # Validate
    error = None
    if not name:
        error = "Business name is required"
    elif not category:
        error = "Category is required"
    elif not city:
        error = "City is required"
    
    if error:
        return render_template("create_business.html", error=error)
    
    # Create business
    try:
        max_clients = int(max_clients)
        if max_clients < 1 or max_clients > 100:
            max_clients = 20
    except:
        max_clients = 20
    
    create_business(user_id, name, category, city, max_clients)
    
    return redirect("/dashboard")

@booking_bp.route("/join", methods=["POST"])
def join_queue():
    db = get_db()

    count = db.execute(
        "SELECT COUNT(*) FROM queue_entries"
    ).fetchone()[0]

    if count >= MAX_CLIENTS:
        return "Queue Full"

    name = request.form["name"]
    number = count + 1

    db.execute(
        "INSERT INTO queue_entries (queue_number, name, status) VALUES (?,?,?)",
        (number, name, "waiting")
    )
    db.commit()

    return redirect("/dashboard")

@booking_bp.route("/done/<int:number>")
def mark_done(number):
    db = get_db()

    db.execute(
        "UPDATE queue_entries SET status='done' WHERE queue_number=?",
        (number,)
    )
    db.commit()

    return redirect("/dashboard")