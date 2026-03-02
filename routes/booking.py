from flask import Blueprint, render_template, request, redirect, session, url_for, current_app
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
    validate_phone_number,
    # PHASE 15: New imports
    mark_entry_completed,
    get_average_service_time,
    estimate_wait_time,
    get_queue_position,
    # PHASE 18: Anti-spam imports
    log_booking,
    check_ip_cooldown,
    cancel_noshow_entries,
    check_daily_ip_limit,
)

booking_bp = Blueprint("booking", __name__)

# ──────────────────────────────────────────────────────────────
# HELPER: safe column access for sqlite3.Row
# sqlite3.Row does NOT support .get() — use this instead
# ──────────────────────────────────────────────────────────────
def row_get(row, key, default=None):
    try:
        val = row[key]
        return val if val is not None else default
    except (IndexError, KeyError):
        return default


# ──────────────────────────────────────────────────────────────
# HELPER: get real client IP (handles reverse proxy)
# ──────────────────────────────────────────────────────────────
def get_client_ip():
    """Return the real client IP, respecting X-Forwarded-For if present."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr


# ──────────────────────────────────────────────────────────────
# HELPER: emit real-time queue update via SocketIO
# ──────────────────────────────────────────────────────────────
def emit_queue_update(business_id, today_queue_id):
    try:
        socketio = current_app.extensions.get('socketio')
        if not socketio:
            print("❌ SocketIO not found in app extensions")
            return

        queue_entries = get_queue_entries(today_queue_id)
        current_count = count_entries_for_queue(today_queue_id)
        business      = get_business_by_id(business_id)
        max_clients   = business["max_clients_per_day"]
        queue_full    = is_queue_full(today_queue_id, max_clients)

        emit_data = {
            'business_id':   business_id,
            'current_count': current_count,
            'max_clients':   max_clients,
            'queue_full':    queue_full,
            'queue_entries': [dict(entry) for entry in queue_entries]
        }

        socketio.emit('queue_updated', emit_data, room=f'business_{business_id}')
        print(f"✅ Emitted queue update for business {business_id}")
    except Exception as e:
        print(f"❌ Error emitting queue update: {e}")
        import traceback
        traceback.print_exc()


# ════════════════════════════════════════════════════════════════
# OWNER ROUTES (PROTECTED)
# ════════════════════════════════════════════════════════════════

@booking_bp.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    user_id  = session["user_id"]
    business = get_business_by_user(user_id)

    if not business:
        return render_template("create_business.html")

    business_id = business["id"]
    today_queue = get_today_queue(business_id)

    if not today_queue:
        create_today_queue(business_id)
        today_queue = get_today_queue(business_id)

    queue_entries    = get_queue_entries(today_queue["id"])
    current_count    = count_entries_for_queue(today_queue["id"])
    max_clients      = business["max_clients_per_day"]
    queue_full       = is_queue_full(today_queue["id"], max_clients)
    avg_service_time = get_average_service_time(business_id)  # PHASE 15

    return render_template(
        "dashboard.html",
        business=business,
        today_queue=today_queue,
        queue_entries=queue_entries,
        current_count=current_count,
        max_clients=max_clients,
        queue_full=queue_full,
        avg_service_time=avg_service_time,
    )


@booking_bp.route("/create-business", methods=["POST"])
def create_business_route():
    if "user_id" not in session:
        return redirect("/login")

    user_id  = session["user_id"]
    existing = get_business_by_user(user_id)
    if existing:
        return redirect("/dashboard")

    name        = request.form.get("name", "").strip()
    category    = request.form.get("category", "").strip()
    city        = request.form.get("city", "").strip()
    max_clients = request.form.get("max_clients", 20)

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

    try:
        max_clients = int(max_clients)
        if max_clients < 1:
            error = "Maximum clients must be at least 1"
        elif max_clients > 500:
            error = "Maximum clients cannot exceed 500"
    except (ValueError, TypeError):
        error = "Invalid number for maximum clients"

    if error:
        return render_template("create_business.html", error=error)

    create_business(user_id, name, category, city, max_clients)
    return redirect("/dashboard")


@booking_bp.route("/settings", methods=["GET", "POST"])
def settings():
    """Business settings page (OWNER ONLY)"""
    if "user_id" not in session:
        return redirect("/login")

    user_id  = session["user_id"]
    business = get_business_by_user(user_id)

    if not business:
        return redirect("/dashboard")

    # ── POST: save settings ──────────────────────────────────────
    if request.method == "POST":
        name        = request.form.get("name", "").strip()
        category    = request.form.get("category", "").strip()
        city        = request.form.get("city", "").strip()
        max_clients = request.form.get("max_clients", business["max_clients_per_day"])

        # PHASE 16: language preference (safe — column may not exist yet)
        language = request.form.get("language", "en").strip()
        if language not in ('en', 'fr', 'ar'):
            language = 'en'

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

        if not error:
            try:
                max_clients = int(max_clients)
                if max_clients < 1:
                    error = "Maximum clients must be at least 1"
                elif max_clients > 500:
                    error = "Maximum clients cannot exceed 500"
            except (ValueError, TypeError):
                error = "Invalid number for maximum clients"

        if error:
            return render_template("settings.html", business=business, error=error)

        # Save core business fields
        update_business(business["id"], name, category, city, max_clients)

        # Save language (safe — silently skips if column doesn't exist yet)
        try:
            conn = get_db()
            conn.execute(
                "UPDATE businesses SET language = ? WHERE id = ?",
                (language, business["id"])
            )
            conn.commit()
            conn.close()
        except Exception:
            pass  # Column missing → run migration_add_language.py

        return redirect("/settings?success=1")

    # ── GET: show form ───────────────────────────────────────────
    success = request.args.get("success")

    # Safe language read — sqlite3.Row has no .get(), use row_get()
    business_lang = row_get(business, "language", "en")

    return render_template(
        "settings.html",
        business=business,
        business_lang=business_lang,
        success=success,
    )


@booking_bp.route("/add-client", methods=["POST"])
def add_client():
    """Add a walk-in client to today's queue (OWNER ONLY)"""
    if "user_id" not in session:
        return redirect("/login")

    user_id  = session["user_id"]
    business = get_business_by_user(user_id)

    if not business:
        return redirect("/dashboard")

    today_queue = get_today_queue(business["id"])
    if not today_queue:
        create_today_queue(business["id"])
        today_queue = get_today_queue(business["id"])

    client_name  = request.form.get("client_name",  "").strip()
    client_phone = request.form.get("client_phone", "").strip()

    def render_dashboard_with_error(error_msg):
        queue_entries    = get_queue_entries(today_queue["id"])
        current_count    = count_entries_for_queue(today_queue["id"])
        max_clients      = business["max_clients_per_day"]
        queue_full       = is_queue_full(today_queue["id"], max_clients)
        avg_service_time = get_average_service_time(business["id"])
        return render_template(
            "dashboard.html",
            business=business,
            today_queue=today_queue,
            queue_entries=queue_entries,
            current_count=current_count,
            max_clients=max_clients,
            queue_full=queue_full,
            avg_service_time=avg_service_time,
            error=error_msg,
        )

    max_clients = business["max_clients_per_day"]
    if is_queue_full(today_queue["id"], max_clients):
        return render_dashboard_with_error("Queue is full for today")

    success, message = add_queue_entry(
        today_queue["id"],
        client_name,
        client_phone if client_phone else None
    )

    if not success:
        return render_dashboard_with_error(message)

    emit_queue_update(business["id"], today_queue["id"])
    return redirect("/dashboard")


@booking_bp.route("/mark-done/<int:entry_id>")
def mark_done(entry_id):
    """Mark a queue entry as completed (OWNER ONLY) — PHASE 15 records timestamp"""
    if "user_id" not in session:
        return redirect("/login")

    user_id  = session["user_id"]
    business = get_business_by_user(user_id)

    if not business:
        return redirect("/dashboard")

    db = get_db()
    entry = db.execute(
        """
        SELECT qe.*, dq.id as queue_id FROM queue_entries qe
        JOIN daily_queues dq ON qe.daily_queue_id = dq.id
        WHERE qe.id = ? AND dq.business_id = ?
        """,
        (entry_id, business["id"])
    ).fetchone()

    if not entry:
        db.close()
        return redirect("/dashboard")

    queue_id = entry["queue_id"]
    db.close()

    mark_entry_completed(entry_id)
    emit_queue_update(business["id"], queue_id)
    return redirect("/dashboard")


@booking_bp.route("/mark-skipped/<int:entry_id>")
def mark_skipped(entry_id):
    """Mark a queue entry as skipped (OWNER ONLY)"""
    if "user_id" not in session:
        return redirect("/login")

    user_id  = session["user_id"]
    business = get_business_by_user(user_id)

    if not business:
        return redirect("/dashboard")

    db = get_db()
    entry = db.execute(
        """
        SELECT qe.*, dq.id as queue_id FROM queue_entries qe
        JOIN daily_queues dq ON qe.daily_queue_id = dq.id
        WHERE qe.id = ? AND dq.business_id = ?
        """,
        (entry_id, business["id"])
    ).fetchone()

    if not entry:
        db.close()
        return redirect("/dashboard")

    db.execute("UPDATE queue_entries SET status = 'skipped' WHERE id = ?", (entry_id,))
    db.commit()
    queue_id = entry["queue_id"]
    db.close()

    emit_queue_update(business["id"], queue_id)
    return redirect("/dashboard")


# ════════════════════════════════════════════════════════════════
# PUBLIC ROUTES (NO LOGIN REQUIRED)
# ════════════════════════════════════════════════════════════════

@booking_bp.route("/b/<int:business_id>", methods=["GET", "POST"])
def public_booking(business_id):
    """
    Public booking page for customers.
    PHASE 18: IP cooldown + daily IP limit + no-show auto-cancel.
    """

    if business_id <= 0:
        return render_template("public_booking.html", error="Invalid business ID", business=None)

    try:
        business = get_business_by_id(business_id)
    except Exception:
        return render_template("public_booking.html",
                               error="An error occurred. Please try again later.", business=None)

    if not business:
        return render_template("public_booking.html", error="Business not found", business=None)

    try:
        today_queue = get_today_queue(business_id)
        if not today_queue:
            create_today_queue(business_id)
            today_queue = get_today_queue(business_id)
    except Exception:
        return render_template("public_booking.html", business=business,
                               error="An error occurred. Please try again later.",
                               current_count=0,
                               max_clients=business["max_clients_per_day"],
                               queue_full=False)

    # ── PHASE 18: Auto-cancel no-shows on every GET ──────────────
    if request.method == "GET":
        cancelled = cancel_noshow_entries(business_id)
        if cancelled > 0:
            print(f"[Phase 18] Auto-cancelled {cancelled} no-show(s) for business {business_id}")
            # Emit update so dashboard/display reflect the cleanup
            emit_queue_update(business_id, today_queue["id"])

    current_count = count_entries_for_queue(today_queue["id"])
    max_clients   = business["max_clients_per_day"]
    queue_full    = is_queue_full(today_queue["id"], max_clients)

    from datetime import date as _date
    today_str  = _date.today().isoformat()
    client_ip  = get_client_ip()

    if request.method == "POST":

        # ── PHASE 18: IP daily limit ─────────────────────────────
        if check_daily_ip_limit(business_id, today_str, client_ip):
            return render_template("public_booking.html", business=business,
                                   current_count=current_count, max_clients=max_clients,
                                   queue_full=queue_full,
                                   error="You have already booked the maximum number of slots today from this device.")

        # ── PHASE 18: IP cooldown ────────────────────────────────
        blocked, minutes_left = check_ip_cooldown(business_id, today_str, client_ip)
        if blocked:
            return render_template("public_booking.html", business=business,
                                   current_count=current_count, max_clients=max_clients,
                                   queue_full=queue_full,
                                   error=f"Please wait {minutes_left} more minute(s) before booking again.")

        client_name  = request.form.get("client_name",  "").strip()
        client_phone = request.form.get("client_phone", "").strip()

        name_valid, name_error = validate_client_name(client_name)
        if not name_valid:
            return render_template("public_booking.html", business=business,
                                   current_count=current_count, max_clients=max_clients,
                                   queue_full=queue_full, error=name_error)

        phone_valid, phone_error = validate_phone_number(client_phone)
        if not phone_valid:
            return render_template("public_booking.html", business=business,
                                   current_count=current_count, max_clients=max_clients,
                                   queue_full=queue_full, error=phone_error)

        if queue_full:
            return render_template("public_booking.html", business=business,
                                   current_count=current_count, max_clients=max_clients,
                                   queue_full=True,
                                   error=f"Sorry, the queue is full for today. Maximum {max_clients} clients per day.")

        success, message = add_queue_entry(today_queue["id"], client_name, client_phone)

        if not success:
            return render_template("public_booking.html", business=business,
                                   current_count=current_count, max_clients=max_clients,
                                   queue_full=queue_full, error=message)

        # ── PHASE 18: Log this booking for future cooldown checks ─
        log_booking(business_id, today_str, client_ip, client_phone)

        emit_queue_update(business_id, today_queue["id"])

        # PHASE 15: position + estimated wait
        new_position   = current_count + 1
        estimated_wait = estimate_wait_time(today_queue["id"], new_position, business_id)

        return render_template(
            "public_booking.html",
            business=business,
            current_count=current_count + 1,
            max_clients=max_clients,
            queue_full=is_queue_full(today_queue["id"], max_clients),
            success=True,
            client_name=client_name,
            position=new_position,
            estimated_wait=estimated_wait,
        )

    return render_template("public_booking.html", business=business,
                           current_count=current_count, max_clients=max_clients,
                           queue_full=queue_full)
