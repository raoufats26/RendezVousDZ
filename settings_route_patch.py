"""
PATCH for routes/booking.py — settings() route
Add language to the POST handler. Make these two targeted changes only.

CHANGE 1: In the POST block, after reading max_clients, add:
    language = request.form.get("language", "en").strip()
    if language not in ('en', 'fr', 'ar'):
        language = 'en'

CHANGE 2: Replace the update_business() call with update_business_with_language()
OR: inline the language update after update_business():

    update_business(business["id"], name, category, city, max_clients)
    # Save language
    from database.db import get_db as _get_db
    _conn = _get_db()
    _conn.execute("UPDATE businesses SET language=? WHERE id=?", (language, business["id"]))
    _conn.commit()
    _conn.close()

That's it. Two additions, nothing else changed.
Full context shown below so you can find the exact location:
"""

# ── EXACT LINES TO FIND (around line 196 in booking.py) ────────
FIND_AFTER = '''        max_clients = request.form.get("max_clients", business["max_clients_per_day"])'''

INSERT_AFTER_FIND_AFTER = '''
        language = request.form.get("language", "en").strip()
        if language not in ('en', 'fr', 'ar'):
            language = 'en'
'''

# ── EXACT LINES TO FIND for the update call ────────────────────
FIND_UPDATE = '''        update_business(business["id"], name, category, city, max_clients)
        
        # Redirect with success message
        return redirect("/settings?success=1")'''

REPLACE_UPDATE = '''        update_business(business["id"], name, category, city, max_clients)

        # Save language preference
        try:
            _conn = get_db()
            _conn.execute("UPDATE businesses SET language=? WHERE id=?",
                          (language, business["id"]))
            _conn.commit()
            _conn.close()
        except Exception:
            pass  # Language column may not exist yet — run migration first

        # Redirect with success message
        return redirect("/settings?success=1")'''
