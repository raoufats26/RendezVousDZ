from flask import Blueprint, render_template, session, redirect, jsonify
from database.db import get_db, get_business_by_user, get_average_service_time

analytics_bp = Blueprint("analytics", __name__)


def get_analytics_data(business_id):
    """
    Pull all analytics data for a business in one place.
    Returns a dict with all chart data and summary stats.
    """
    conn = get_db()

    # ── 1. Last 7 days: daily client count ──────────────────────────────────
    daily_counts = conn.execute("""
        SELECT 
            dq.date,
            COUNT(qe.id) as total,
            SUM(CASE WHEN qe.status = 'completed' THEN 1 ELSE 0 END) as completed,
            SUM(CASE WHEN qe.status = 'skipped'   THEN 1 ELSE 0 END) as skipped,
            SUM(CASE WHEN qe.status = 'waiting'   THEN 1 ELSE 0 END) as waiting
        FROM daily_queues dq
        LEFT JOIN queue_entries qe ON qe.daily_queue_id = dq.id
        WHERE dq.business_id = ?
          AND dq.date >= date('now', '-6 days')
        GROUP BY dq.date
        ORDER BY dq.date ASC
    """, (business_id,)).fetchall()

    # ── 2. Peak hours – hour of day when clients arrive most ────────────────
    peak_hours = conn.execute("""
        SELECT 
            CAST(strftime('%H', qe.created_at) AS INTEGER) as hour,
            COUNT(*) as count
        FROM queue_entries qe
        JOIN daily_queues dq ON qe.daily_queue_id = dq.id
        WHERE dq.business_id = ?
          AND dq.date >= date('now', '-29 days')
        GROUP BY hour
        ORDER BY hour ASC
    """, (business_id,)).fetchall()

    # ── 3. Weekly performance – last 4 weeks ────────────────────────────────
    weekly = conn.execute("""
        SELECT 
            strftime('%W', dq.date) as week_num,
            MIN(dq.date)            as week_start,
            COUNT(qe.id)            as total,
            SUM(CASE WHEN qe.status = 'completed' THEN 1 ELSE 0 END) as completed,
            SUM(CASE WHEN qe.status = 'skipped'   THEN 1 ELSE 0 END) as skipped
        FROM daily_queues dq
        LEFT JOIN queue_entries qe ON qe.daily_queue_id = dq.id
        WHERE dq.business_id = ?
          AND dq.date >= date('now', '-27 days')
        GROUP BY week_num
        ORDER BY week_num ASC
    """, (business_id,)).fetchall()

    # ── 4. Overall summary stats ─────────────────────────────────────────────
    summary = conn.execute("""
        SELECT
            COUNT(qe.id)                                                         as total_all_time,
            SUM(CASE WHEN qe.status = 'completed' THEN 1 ELSE 0 END)            as total_completed,
            SUM(CASE WHEN qe.status = 'skipped'   THEN 1 ELSE 0 END)            as total_skipped,
            SUM(CASE WHEN dq.date  = date('now')  THEN 1 ELSE 0 END)            as today_total,
            SUM(CASE WHEN dq.date >= date('now','-6 days') THEN 1 ELSE 0 END)   as week_total
        FROM queue_entries qe
        JOIN daily_queues dq ON qe.daily_queue_id = dq.id
        WHERE dq.business_id = ?
    """, (business_id,)).fetchone()

    # ── 5. Busiest day of week (0=Mon…6=Sun in Python, but SQLite %w 0=Sun) ─
    busiest_dow = conn.execute("""
        SELECT 
            strftime('%w', dq.date) as dow,
            COUNT(qe.id)            as count
        FROM queue_entries qe
        JOIN daily_queues dq ON qe.daily_queue_id = dq.id
        WHERE dq.business_id = ?
          AND dq.date >= date('now', '-29 days')
        GROUP BY dow
        ORDER BY count DESC
        LIMIT 1
    """, (business_id,)).fetchone()

    conn.close()

    # ── Format daily data ────────────────────────────────────────────────────
    day_labels, day_totals, day_completed, day_skipped = [], [], [], []
    for row in daily_counts:
        # short day name from YYYY-MM-DD
        import datetime
        d = datetime.date.fromisoformat(row["date"])
        day_labels.append(d.strftime("%a %d"))
        day_totals.append(row["total"] or 0)
        day_completed.append(row["completed"] or 0)
        day_skipped.append(row["skipped"] or 0)

    # ── Format peak-hours data (fill missing hours with 0) ──────────────────
    hour_counts = {row["hour"]: row["count"] for row in peak_hours}
    peak_labels = [f"{h:02d}:00" for h in range(8, 21)]   # 08:00–20:00
    peak_values = [hour_counts.get(h, 0) for h in range(8, 21)]

    # ── Format weekly data ───────────────────────────────────────────────────
    import datetime
    week_labels, week_totals, week_completed = [], [], []
    for row in weekly:
        d = datetime.date.fromisoformat(row["week_start"])
        week_labels.append(f"Week of {d.strftime('%b %d')}")
        week_totals.append(row["total"] or 0)
        week_completed.append(row["completed"] or 0)

    # ── No-show rate ─────────────────────────────────────────────────────────
    total_all   = summary["total_all_time"]   or 0
    total_comp  = summary["total_completed"]  or 0
    total_skip  = summary["total_skipped"]    or 0
    noshow_rate = round((total_skip / total_all * 100), 1) if total_all > 0 else 0
    complete_rate = round((total_comp / total_all * 100), 1) if total_all > 0 else 0

    # ── DOW name ─────────────────────────────────────────────────────────────
    dow_names = {
        "0": "Sunday", "1": "Monday", "2": "Tuesday",
        "3": "Wednesday", "4": "Thursday", "5": "Friday", "6": "Saturday"
    }
    busiest_day_name = "N/A"
    if busiest_dow:
        busiest_day_name = dow_names.get(str(busiest_dow["dow"]), "N/A")

    avg_service = get_average_service_time(business_id)

    return {
        # Chart data
        "day_labels":    day_labels,
        "day_totals":    day_totals,
        "day_completed": day_completed,
        "day_skipped":   day_skipped,
        "peak_labels":   peak_labels,
        "peak_values":   peak_values,
        "week_labels":   week_labels,
        "week_totals":   week_totals,
        "week_completed": week_completed,
        # Summary cards
        "total_all_time":  total_all,
        "today_total":     summary["today_total"]  or 0,
        "week_total":      summary["week_total"]   or 0,
        "total_completed": total_comp,
        "total_skipped":   total_skip,
        "noshow_rate":     noshow_rate,
        "complete_rate":   complete_rate,
        "avg_service_time": avg_service,
        "busiest_day":     busiest_day_name,
    }


@analytics_bp.route("/analytics")
def analytics():
    if "user_id" not in session:
        return redirect("/login")

    from database.db import get_business_by_user
    business = get_business_by_user(session["user_id"])

    if not business:
        return redirect("/dashboard")

    data = get_analytics_data(business["id"])
    return render_template("analytics.html", business=business, data=data)


@analytics_bp.route("/analytics/api")
def analytics_api():
    """JSON endpoint — optional, for future live refresh."""
    if "user_id" not in session:
        return jsonify({"error": "unauthorized"}), 401

    from database.db import get_business_by_user
    business = get_business_by_user(session["user_id"])
    if not business:
        return jsonify({"error": "no business"}), 404

    return jsonify(get_analytics_data(business["id"]))
