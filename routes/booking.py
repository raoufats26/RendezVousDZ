from flask import Blueprint, render_template, request, redirect, session, flash
from database.db import (
    get_db, 
    get_business_by_user, 
    create_business, 
    get_today_queue, 
    create_today_queue,
    count_entries_for_queue,
    is_queue_full,
    add_queue_entry,
    get_queue_entries
)

booking_bp = Blueprint("booking", __name__)

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
    
    # User has business - ensure today's queue exists
    business_id = business["id"]
    
    # Check if today's queue exists
    today_queue = get_today_queue(business_id)
    
    if not today_queue:
        # Create today's queue (safe operation - won't duplicate)
        create_today_queue(business_id)
        # Fetch it again to confirm
        today_queue = get_today_queue(business_id)
    
    # Get queue entries for today
    queue_entries = get_queue_entries(today_queue["id"])
    
    # Get current count and max
    current_count = count_entries_for_queue(today_queue["id"])
    max_clients = business["max_clients_per_day"]
    
    # Check if queue is full
    queue_full = is_queue_full(today_queue["id"], max_clients)

    return render_template(
        "dashboard.html", 
        business=business, 
        today_queue=today_queue,
        queue_entries=queue_entries,
        current_count=current_count,
        max_clients=max_clients,
        queue_full=queue_full
    )

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

@booking_bp.route("/add-client", methods=["POST"])
def add_client():
    """Add a client to today's queue with limit enforcement"""
    if "user_id" not in session:
        return redirect("/login")
    
    user_id = session["user_id"]
    business = get_business_by_user(user_id)
    
    if not business:
        return redirect("/dashboard")
    
    # Get today's queue
    today_queue = get_today_queue(business["id"])
    
    if not today_queue:
        return redirect("/dashboard")
    
    # Get form data
    client_name = request.form.get("client_name", "").strip()
    client_phone = request.form.get("client_phone", "").strip()
    
    if not client_name:
        return render_template(
            "dashboard.html",
            business=business,
            today_queue=today_queue,
            queue_entries=get_queue_entries(today_queue["id"]),
            current_count=count_entries_for_queue(today_queue["id"]),
            max_clients=business["max_clients_per_day"],
            queue_full=is_queue_full(today_queue["id"], business["max_clients_per_day"]),
            error="Client name is required"
        )
    
    # CHECK LIMIT BEFORE ADDING
    if is_queue_full(today_queue["id"], business["max_clients_per_day"]):
        return render_template(
            "dashboard.html",
            business=business,
            today_queue=today_queue,
            queue_entries=get_queue_entries(today_queue["id"]),
            current_count=count_entries_for_queue(today_queue["id"]),
            max_clients=business["max_clients_per_day"],
            queue_full=True,
            error=f"Queue is full. Maximum {business['max_clients_per_day']} clients per day."
        )
    
    # Add client to queue
    success, message = add_queue_entry(today_queue["id"], client_name, client_phone)
    
    if not success:
        return render_template(
            "dashboard.html",
            business=business,
            today_queue=today_queue,
            queue_entries=get_queue_entries(today_queue["id"]),
            current_count=count_entries_for_queue(today_queue["id"]),
            max_clients=business["max_clients_per_day"],
            queue_full=is_queue_full(today_queue["id"], business["max_clients_per_day"]),
            error=message
        )
    
    return redirect("/dashboard")

@booking_bp.route("/mark-done/<int:entry_id>")
def mark_done(entry_id):
    """Mark a queue entry as done"""
    if "user_id" not in session:
        return redirect("/login")
    
    db = get_db()
    db.execute(
        "UPDATE queue_entries SET status = 'done' WHERE id = ?",
        (entry_id,)
    )
    db.commit()
    
    return redirect("/dashboard")

@booking_bp.route("/mark-skipped/<int:entry_id>")
def mark_skipped(entry_id):
    """Mark a queue entry as skipped"""
    if "user_id" not in session:
        return redirect("/login")
    
    db = get_db()
    db.execute(
        "UPDATE queue_entries SET status = 'skipped' WHERE id = ?",
        (entry_id,)
    )
    db.commit()
    
    return redirect("/dashboard")