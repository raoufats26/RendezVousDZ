import datetime
from flask import Blueprint, render_template, session, redirect, jsonify
from database.db import get_db, get_business_by_user, get_average_service_time, _execute, USE_POSTGRES

analytics_bp = Blueprint("analytics", __name__)


def get_analytics_data(business_id):
    conn = get_db()

    if USE_POSTGRES:
        # ── 1. Last 7 days ───────────────────────────────────────────────────
        daily_counts = _execute(conn, """
            SELECT
                dq.date::text as date,
                COUNT(qe.id) as total,
                SUM(CASE WHEN qe.status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN qe.status = 'skipped'   THEN 1 ELSE 0 END) as skipped,
                SUM(CASE WHEN qe.status = 'waiting'   THEN 1 ELSE 0 END) as waiting
            FROM daily_queues dq
            LEFT JOIN queue_entries qe ON qe.daily_queue_id = dq.id
            WHERE dq.business_id = %s
              AND dq.date::date >= CURRENT_DATE - INTERVAL '6 days'
            GROUP BY dq.date
            ORDER BY dq.date ASC
        """, (business_id,)).fetchall()

        # ── 2. Peak hours ────────────────────────────────────────────────────
        peak_hours = _execute(conn, """
            SELECT
                EXTRACT(HOUR FROM qe.created_at)::integer as hour,
                COUNT(*) as count
            FROM queue_entries qe
            JOIN daily_queues dq ON qe.daily_queue_id = dq.id
            WHERE dq.business_id = %s
              AND dq.date::date >= CURRENT_DATE - INTERVAL '29 days'
            GROUP BY hour
            ORDER BY hour ASC
        """, (business_id,)).fetchall()

        # ── 3. Weekly performance ────────────────────────────────────────────
        weekly = _execute(conn, """
            SELECT
                TO_CHAR(dq.date::date, 'IW') as week_num,
                MIN(dq.date)::text            as week_start,
                COUNT(qe.id)                  as total,
                SUM(CASE WHEN qe.status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN qe.status = 'skipped'   THEN 1 ELSE 0 END) as skipped
            FROM daily_queues dq
            LEFT JOIN queue_entries qe ON qe.daily_queue_id = dq.id
            WHERE dq.business_id = %s
              AND dq.date::date >= CURRENT_DATE - INTERVAL '27 days'
            GROUP BY week_num
            ORDER BY week_num ASC
        """, (business_id,)).fetchall()

        # ── 4. Summary stats ─────────────────────────────────────────────────
        summary = _execute(conn, """
            SELECT
                COUNT(qe.id) as total_all_time,
                SUM(CASE WHEN qe.status = 'completed' THEN 1 ELSE 0 END) as total_completed,
                SUM(CASE WHEN qe.status = 'skipped'   THEN 1 ELSE 0 END) as total_skipped,
                SUM(CASE WHEN dq.date::date = CURRENT_DATE THEN 1 ELSE 0 END) as today_total,
                SUM(CASE WHEN dq.date::date >= CURRENT_DATE - INTERVAL '6 days' THEN 1 ELSE 0 END) as week_total
            FROM queue_entries qe
            JOIN daily_queues dq ON qe.daily_queue_id = dq.id
            WHERE dq.business_id = %s
        """, (business_id,)).fetchone()

        # ── 5. Busiest day of week ────────────────────────────────────────────
        busiest_dow = _execute(conn, """
            SELECT
                EXTRACT(DOW FROM dq.date::date)::text as dow,
                COUNT(qe.id) as count
            FROM queue_entries qe
            JOIN daily_queues dq ON qe.daily_queue_id = dq.id
            WHERE dq.business_id = %s
              AND dq.date::date >= CURRENT_DATE - INTERVAL '29 days'
            GROUP BY dow
            ORDER BY count DESC
            LIMIT 1
        """, (business_id,)).fetchone()

    else:
        # ── SQLite queries (original) ────────────────────────────────────────
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

        summary = conn.execute("""
            SELECT
                COUNT(qe.id)                                                       as total_all_time,
                SUM(CASE WHEN qe.status = 'completed' THEN 1 ELSE 0 END)          as total_completed,
                SUM(CASE WHEN qe.status = 'skipped'   THEN 1 ELSE 0 END)          as total_skipped,
                SUM(CASE WHEN dq.date  = date('now')  THEN 1 ELSE 0 END)          as today_total,
                SUM(CASE WHEN dq.date >= date('now','-6 days') THEN 1 ELSE 0 END) as week_total
            FROM queue_entries qe
            JOIN daily_queues dq ON qe.daily_queue_id = dq.id
            WHERE dq.business_id = ?
        """, (business_id,)).fetchone()

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

    # Convert rows to dicts for uniform access
    if USE_POSTGRES:
        daily_counts = [dict(r) for r in daily_counts]
        peak_hours   = [dict(r) for r in peak_hours]
        weekly       = [dict(r) for r in weekly]
        summary      = dict(summary) if summary else {}
        busiest_dow  = dict(busiest_dow) if busiest_dow else None

    # ── Format daily data ────────────────────────────────────────────────────
    day_labels, day_totals, day_completed, day_skipped = [], [], [], []
    for row in daily_counts:
        date_val = row["date"]
        if not isinstance(date_val, str):
            date_val = str(date_val)
        d = datetime.date.fromisoformat(date_val[:10])
        day_labels.append(d.strftime("%a %d"))
        day_totals.append(row["total"] or 0)
        day_completed.append(row["completed"] or 0)
        day_skipped.append(row["skipped"] or 0)

    # ── Format peak-hours data ───────────────────────────────────────────────
    hour_counts = {int(row["hour"]): row["count"] for row in peak_hours}
    peak_labels = [f"{h:02d}:00" for h in range(8, 21)]
    peak_values = [hour_counts.get(h, 0) for h in range(8, 21)]

    # ── Format weekly data ───────────────────────────────────────────────────
    week_labels, week_totals, week_completed = [], [], []
    for row in weekly:
        date_val = row["week_start"]
        if not isinstance(date_val, str):
            date_val = str(date_val)
        d = datetime.date.fromisoformat(date_val[:10])
        week_labels.append(f"Week of {d.strftime('%b %d')}")
        week_totals.append(row["total"] or 0)
        week_completed.append(row["completed"] or 0)

    # ── Summary stats ────────────────────────────────────────────────────────
    total_all   = summary.get("total_all_time")  or 0
    total_comp  = summary.get("total_completed") or 0
    total_skip  = summary.get("total_skipped")   or 0
    noshow_rate   = round((total_skip / total_all * 100), 1) if total_all > 0 else 0
    complete_rate = round((total_comp / total_all * 100), 1) if total_all > 0 else 0

    # ── Busiest day name ─────────────────────────────────────────────────────
    dow_names = {
        "0": "Sunday", "1": "Monday", "2": "Tuesday",
        "3": "Wednesday", "4": "Thursday", "5": "Friday", "6": "Saturday"
    }
    busiest_day_name = "N/A"
    if busiest_dow:
        busiest_day_name = dow_names.get(str(int(float(busiest_dow["dow"]))), "N/A")

    avg_service = get_average_service_time(business_id)

    return {
        "day_labels":     day_labels,
        "day_totals":     day_totals,
        "day_completed":  day_completed,
        "day_skipped":    day_skipped,
        "peak_labels":    peak_labels,
        "peak_values":    peak_values,
        "week_labels":    week_labels,
        "week_totals":    week_totals,
        "week_completed": week_completed,
        "total_all_time":  total_all,
        "today_total":     summary.get("today_total") or 0,
        "week_total":      summary.get("week_total")  or 0,
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

    business = get_business_by_user(session["user_id"])
    if not business:
        return redirect("/dashboard")

    data = get_analytics_data(business["id"])
    return render_template("analytics.html", business=business, data=data)


@analytics_bp.route("/analytics/api")
def analytics_api():
    if "user_id" not in session:
        return jsonify({"error": "unauthorized"}), 401

    business = get_business_by_user(session["user_id"])
    if not business:
        return jsonify({"error": "no business"}), 404

    return jsonify(get_analytics_data(business["id"]))
