from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
import os
from datetime import datetime
from contextlib import contextmanager

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-demo-secret")
DATABASE = os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "queue.db"))

SERVICES = {
    "General Enquiry": 5,
    "Payments": 7,
    "Customer Support": 10,
    "Document Verification": 8,
}

@contextmanager
def db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db():
    with db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_no TEXT UNIQUE NOT NULL,
                customer_name TEXT NOT NULL,
                service TEXT NOT NULL,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Waiting',
                served_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        conn.execute("INSERT OR IGNORE INTO settings(key, value) VALUES ('next_ticket', '1')")

def get_stats(conn):
    waiting = conn.execute("SELECT COUNT(*) FROM tickets WHERE status='Waiting'").fetchone()[0]
    serving = conn.execute("SELECT COUNT(*) FROM tickets WHERE status='Serving'").fetchone()[0]
    served_today = conn.execute(
        "SELECT COUNT(*) FROM tickets WHERE status='Served' AND date(served_at)=date('now','localtime')"
    ).fetchone()[0]
    total_today = conn.execute(
        "SELECT COUNT(*) FROM tickets WHERE date(created_at)=date('now','localtime')"
    ).fetchone()[0]
    return {"waiting": waiting, "serving": serving, "served_today": served_today, "total_today": total_today}

@app.route("/")
def index():
    with db_connection() as conn:
        stats = get_stats(conn)
        queue = conn.execute("""
            SELECT * FROM tickets WHERE status IN ('Waiting','Serving')
            ORDER BY CASE status WHEN 'Serving' THEN 0 ELSE 1 END, id ASC
        """).fetchall()
        recent = conn.execute("SELECT * FROM tickets ORDER BY id DESC LIMIT 6").fetchall()
    return render_template("index.html", stats=stats, queue=queue, recent=recent, services=SERVICES)

@app.route("/join", methods=["POST"])
def join_queue():
    name = request.form.get("customer_name", "").strip()
    service = request.form.get("service", "").strip()
    if not name or len(name) > 80:
        flash("Please enter a name (up to 80 characters).", "error")
        return redirect(url_for("index"))
    if service not in SERVICES:
        flash("Please choose a valid service.", "error")
        return redirect(url_for("index"))

    with db_connection() as conn:
        today_prefix = datetime.now().strftime("%y%m%d")
        row = conn.execute("SELECT value FROM settings WHERE key='next_ticket'").fetchone()
        number = int(row["value"]) if row else 1
        ticket_no = f"Q{today_prefix}-{number:03d}"
        conn.execute("UPDATE settings SET value=? WHERE key='next_ticket'", (str(number + 1),))
        conn.execute(
            "INSERT INTO tickets(ticket_no, customer_name, service, created_at, status) VALUES (?,?,?,?, 'Waiting')",
            (ticket_no, name, service, datetime.now().isoformat(timespec="seconds"))
        )
        ticket_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    return redirect(url_for("ticket", ticket_id=ticket_id))

@app.route("/ticket/<int:ticket_id>")
def ticket(ticket_id):
    with db_connection() as conn:
        item = conn.execute("SELECT * FROM tickets WHERE id=?", (ticket_id,)).fetchone()
        if item:
            ahead = conn.execute(
                "SELECT COUNT(*) FROM tickets WHERE status='Waiting' AND id < ?", (ticket_id,)
            ).fetchone()[0]
        else:
            ahead = 0
    if not item:
        flash("Ticket not found.", "error")
        return redirect(url_for("index"))
    wait_minutes = ahead * SERVICES.get(item["service"], 5)
    return render_template("ticket.html", item=item, ahead=ahead, wait_minutes=wait_minutes)

@app.route("/admin")
def admin():
    with db_connection() as conn:
        stats = get_stats(conn)
        queue = conn.execute("""
            SELECT * FROM tickets WHERE status IN ('Waiting','Serving')
            ORDER BY CASE status WHEN 'Serving' THEN 0 ELSE 1 END, id ASC
        """).fetchall()
        history = conn.execute("SELECT * FROM tickets ORDER BY id DESC LIMIT 30").fetchall()
    return render_template("admin.html", stats=stats, queue=queue, history=history)

@app.route("/admin/next", methods=["POST"])
def call_next():
    with db_connection() as conn:
        current = conn.execute("SELECT id FROM tickets WHERE status='Serving' ORDER BY id ASC LIMIT 1").fetchone()
        if current:
            conn.execute("UPDATE tickets SET status='Served', served_at=? WHERE id=?",
                         (datetime.now().isoformat(timespec="seconds"), current["id"]))
        next_item = conn.execute("SELECT id FROM tickets WHERE status='Waiting' ORDER BY id ASC LIMIT 1").fetchone()
        if next_item:
            conn.execute("UPDATE tickets SET status='Serving' WHERE id=?", (next_item["id"],))
            flash("Next ticket has been called.", "success")
        else:
            flash("There are no waiting tickets.", "info")
    return redirect(url_for("admin"))

@app.route("/admin/serve/<int:ticket_id>", methods=["POST"])
def serve_ticket(ticket_id):
    with db_connection() as conn:
        conn.execute("UPDATE tickets SET status='Served', served_at=? WHERE id=? AND status IN ('Waiting','Serving')",
                     (datetime.now().isoformat(timespec="seconds"), ticket_id))
    flash("Ticket marked as served.", "success")
    return redirect(url_for("admin"))

@app.route("/admin/cancel/<int:ticket_id>", methods=["POST"])
def cancel_ticket(ticket_id):
    with db_connection() as conn:
        conn.execute("UPDATE tickets SET status='Cancelled' WHERE id=? AND status IN ('Waiting','Serving')", (ticket_id,))
    flash("Ticket cancelled.", "info")
    return redirect(url_for("admin"))

@app.route("/admin/reset", methods=["POST"])
def reset_queue():
    confirmation = request.form.get("confirmation", "").strip()
    if confirmation != "RESET":
        flash("Type RESET to confirm clearing all queue records.", "error")
        return redirect(url_for("admin"))
    with db_connection() as conn:
        conn.execute("DELETE FROM tickets")
        conn.execute("UPDATE settings SET value='1' WHERE key='next_ticket'")
    flash("Queue history cleared.", "success")
    return redirect(url_for("admin"))

@app.route("/api/queue")
def queue_api():
    with db_connection() as conn:
        stats = get_stats(conn)
        rows = conn.execute("""
            SELECT ticket_no, customer_name, service, status, created_at
            FROM tickets WHERE status IN ('Waiting','Serving')
            ORDER BY CASE status WHEN 'Serving' THEN 0 ELSE 1 END, id ASC
        """).fetchall()
    return jsonify({"stats": stats, "queue": [dict(row) for row in rows]})

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

init_db()

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "1") == "1", host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
