"""
routes/display.py
PHASE 16: Digital Display Mode — /display/<business_id>
Public route, no login required.
Does NOT touch booking.py or auth.py.
"""
from flask import Blueprint, render_template, session
from database.db import (
    get_business_by_id,
    get_today_queue,
    get_queue_entries,
)

display_bp = Blueprint("display", __name__)

# Language lookup — falls back to 'en'
SUPPORTED_LANGS = {'en', 'fr', 'ar'}


@display_bp.route("/display/<int:business_id>")
def display(business_id):
    """
    Full-screen digital display for waiting clients.
    Shows: Now Serving / Next in Line / Upcoming queue.
    Updates in real-time via SocketIO (same room as dashboard).
    """
    if business_id <= 0:
        return render_template("display.html",
                               business=None, entries=[], lang='en'), 404

    business = get_business_by_id(business_id)
    if not business:
        return render_template("display.html",
                               business=None, entries=[], lang='en'), 404

    # Get today's queue and entries
    today_queue = get_today_queue(business_id)
    entries = []
    if today_queue:
        entries = [dict(e) for e in get_queue_entries(today_queue["id"])]

    # Determine language from business settings (stored in DB, default 'en')
    lang = 'en'
    try:
        lang = business["language"] if business["language"] in SUPPORTED_LANGS else 'en'
    except (KeyError, TypeError):
        lang = 'en'

    return render_template(
        "display.html",
        business=business,
        entries=entries,
        lang=lang,
    )
