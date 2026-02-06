from flask import Blueprint, render_template, request, redirect, session
from database.db import get_db

booking_bp = Blueprint("booking", __name__)

MAX_CLIENTS = 20

@booking_bp.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    db = get_db()
    queue = db.execute(
        "SELECT * FROM queue_entries ORDER BY queue_number"
    ).fetchall()

    return render_template("dashboard.html", queue=queue)

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
