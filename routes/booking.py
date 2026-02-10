from flask import Blueprint, render_template, request, redirect, session, url_for
from database.db import (
    get_db, 
    get_business_by_user, 
    create_business,
    update_business,
    get_today_queue, 
    create_today_queue,
    count_entries_for_queue,
    is_queue_full,
    add_queue_entry,
    get_queue_entries,
    get_business_by_id,
    validate_client_name,
    validate_phone_number
)

booking_bp = Blueprint("booking", __name__)

# ========================================
# OWNER ROUTES (PROTECTED)
# ========================================

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
    elif len(name) < 2:
        error = "Business name must be at least 2 characters"
    elif len(name) > 100:
        error = "Business name is too long (maximum 100 characters)"
    elif not category:
        error = "Category is required"
    elif not city:
        error = "City is required"
    elif len(city) < 2:
        error = "City name must be at least 2 characters"
    
    if error:
        return render_template("create_business.html", error=error)
    
    # Validate and sanitize max_clients
    try:
        max_clients = int(max_clients)
        if max_clients < 1:
            error = "Maximum clients must be at least 1"
        elif max_clients > 100:
            error = "Maximum clients cannot exceed 100"
    except (ValueError, TypeError):
        error = "Invalid number for maximum clients"
    
    if error:
        return render_template("create_business.html", error=error)
    
    # Create business
    create_business(user_id, name, category, city, max_clients)
    
    return redirect("/dashboard")

@booking_bp.route("/settings", methods=["GET", "POST"])
def settings():
    """Business settings page (OWNER ONLY)"""
    if "user_id" not in session:
        return redirect("/login")
    
    user_id = session["user_id"]
    business = get_business_by_user(user_id)
    
    # No business = redirect to create
    if not business:
        return redirect("/dashboard")
    
    # Handle POST (update settings)
    if request.method == "POST":
        # Get form data
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "").strip()
        city = request.form.get("city", "").strip()
        max_clients = request.form.get("max_clients", business["max_clients_per_day"])
        
        # Validate
        error = None
        if not name:
            error = "Business name is required"
        elif len(name) < 2:
            error = "Business name must be at least 2 characters"
        elif len(name) > 100:
            error = "Business name is too long (maximum 100 characters)"
        elif not category:
            error = "Category is required"
        elif not city:
            error = "City is required"
        elif len(city) < 2:
            error = "City name must be at least 2 characters"
        
        # Validate max_clients
        if not error:
            try:
                max_clients = int(max_clients)
                if max_clients < 1:
                    error = "Maximum clients must be at least 1"
                elif max_clients > 100:
                    error = "Maximum clients cannot exceed 100"
            except (ValueError, TypeError):
                error = "Invalid number for maximum clients"
        
        # If validation failed, show error
        if error:
            return render_template("settings.html", business=business, error=error)
        
        # Update business (safe - does not affect existing queues)
        update_business(business["id"], name, category, city, max_clients)
        
        # Redirect with success message
        return redirect("/settings?success=1")
    
    # Handle GET (show form)
    success = request.args.get("success")
    return render_template("settings.html", business=business, success=success)

@booking_bp.route("/add-client", methods=["POST"])
def add_client():
    """Add a walk-in client to today's queue (OWNER ONLY)"""
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
    
    # Helper function to render dashboard with error
    def render_dashboard_with_error(error_msg):
        return render_template(
            "dashboard.html",
            business=business,
            today_queue=today_queue,
            queue_entries=get_queue_entries(today_queue["id"]),
            current_count=count_entries_for_queue(today_queue["id"]),
            max_clients=business["max_clients_per_day"],
            queue_full=is_queue_full(today_queue["id"], business["max_clients_per_day"]),
            error=error_msg
        )
    
    # Get form data
    client_name = request.form.get("client_name", "").strip()
    client_phone = request.form.get("client_phone", "").strip()
    
    # Validate name
    name_valid, name_error = validate_client_name(client_name)
    if not name_valid:
        return render_dashboard_with_error(name_error)
    
    # Validate phone (optional for walk-ins, but if provided must be valid)
    if client_phone:
        phone_valid, phone_error = validate_phone_number(client_phone)
        if not phone_valid:
            return render_dashboard_with_error(phone_error)
    
    # CHECK LIMIT BEFORE ADDING
    if is_queue_full(today_queue["id"], business["max_clients_per_day"]):
        return render_dashboard_with_error(
            f"Queue is full. Maximum {business['max_clients_per_day']} clients per day."
        )
    
    # Add client to queue (validation happens inside add_queue_entry)
    success, message = add_queue_entry(today_queue["id"], client_name, client_phone if client_phone else None)
    
    if not success:
        return render_dashboard_with_error(message)
    
    return redirect("/dashboard")

@booking_bp.route("/mark-done/<int:entry_id>")
def mark_done(entry_id):
    """Mark a queue entry as done (OWNER ONLY)"""
    if "user_id" not in session:
        return redirect("/login")
    
    # Verify the entry belongs to this user's business
    user_id = session["user_id"]
    business = get_business_by_user(user_id)
    
    if not business:
        return redirect("/dashboard")
    
    db = get_db()
    
    # Check entry exists and belongs to this business
    entry = db.execute(
        """
        SELECT qe.* FROM queue_entries qe
        JOIN daily_queues dq ON qe.daily_queue_id = dq.id
        WHERE qe.id = ? AND dq.business_id = ?
        """,
        (entry_id, business["id"])
    ).fetchone()
    
    if not entry:
        db.close()
        return redirect("/dashboard")
    
    # Update status
    db.execute(
        "UPDATE queue_entries SET status = 'done' WHERE id = ?",
        (entry_id,)
    )
    db.commit()
    db.close()
    
    return redirect("/dashboard")

@booking_bp.route("/mark-skipped/<int:entry_id>")
def mark_skipped(entry_id):
    """Mark a queue entry as skipped (OWNER ONLY)"""
    if "user_id" not in session:
        return redirect("/login")
    
    # Verify the entry belongs to this user's business
    user_id = session["user_id"]
    business = get_business_by_user(user_id)
    
    if not business:
        return redirect("/dashboard")
    
    db = get_db()
    
    # Check entry exists and belongs to this business
    entry = db.execute(
        """
        SELECT qe.* FROM queue_entries qe
        JOIN daily_queues dq ON qe.daily_queue_id = dq.id
        WHERE qe.id = ? AND dq.business_id = ?
        """,
        (entry_id, business["id"])
    ).fetchone()
    
    if not entry:
        db.close()
        return redirect("/dashboard")
    
    # Update status
    db.execute(
        "UPDATE queue_entries SET status = 'skipped' WHERE id = ?",
        (entry_id,)
    )
    db.commit()
    db.close()
    
    return redirect("/dashboard")


# ========================================
# PUBLIC ROUTES (NO LOGIN REQUIRED)
# ========================================

@booking_bp.route("/b/<int:business_id>", methods=["GET", "POST"])
def public_booking(business_id):
    """Public booking page for customers (NO LOGIN REQUIRED)"""
    
    # Validate business_id is positive
    if business_id <= 0:
        return render_template(
            "public_booking.html",
            error="Invalid business ID",
            business=None
        )
    
    # Get business
    try:
        business = get_business_by_id(business_id)
    except Exception as e:
        return render_template(
            "public_booking.html",
            error="An error occurred. Please try again later.",
            business=None
        )
    
    # Business not found
    if not business:
        return render_template(
            "public_booking.html",
            error="Business not found",
            business=None
        )
    
    # Ensure today's queue exists
    try:
        today_queue = get_today_queue(business_id)
        
        if not today_queue:
            create_today_queue(business_id)
            today_queue = get_today_queue(business_id)
    except Exception as e:
        return render_template(
            "public_booking.html",
            business=business,
            error="An error occurred. Please try again later.",
            current_count=0,
            max_clients=business["max_clients_per_day"],
            queue_full=False
        )
    
    # Get current count
    current_count = count_entries_for_queue(today_queue["id"])
    max_clients = business["max_clients_per_day"]
    queue_full = is_queue_full(today_queue["id"], max_clients)
    
    # Handle POST (customer submission)
    if request.method == "POST":
        client_name = request.form.get("client_name", "").strip()
        client_phone = request.form.get("client_phone", "").strip()
        
        # Validate name
        name_valid, name_error = validate_client_name(client_name)
        if not name_valid:
            return render_template(
                "public_booking.html",
                business=business,
                current_count=current_count,
                max_clients=max_clients,
                queue_full=queue_full,
                error=name_error
            )
        
        # Validate phone (required for public bookings)
        phone_valid, phone_error = validate_phone_number(client_phone)
        if not phone_valid:
            return render_template(
                "public_booking.html",
                business=business,
                current_count=current_count,
                max_clients=max_clients,
                queue_full=queue_full,
                error=phone_error
            )
        
        # Check if queue is full
        if queue_full:
            return render_template(
                "public_booking.html",
                business=business,
                current_count=current_count,
                max_clients=max_clients,
                queue_full=True,
                error=f"Sorry, the queue is full for today. Maximum {max_clients} clients per day."
            )
        
        # Add to queue (validation and duplicate check happens inside)
        success, message = add_queue_entry(today_queue["id"], client_name, client_phone)
        
        if not success:
            return render_template(
                "public_booking.html",
                business=business,
                current_count=current_count,
                max_clients=max_clients,
                queue_full=queue_full,
                error=message
            )
        
        # Success - show confirmation
        new_position = current_count + 1
        return render_template(
            "public_booking.html",
            business=business,
            current_count=current_count + 1,
            max_clients=max_clients,
            queue_full=is_queue_full(today_queue["id"], max_clients),
            success=True,
            client_name=client_name,
            position=new_position
        )
    
    # Handle GET (show form)
    return render_template(
        "public_booking.html",
        business=business,
        current_count=current_count,
        max_clients=max_clients,
        queue_full=queue_full
    )
