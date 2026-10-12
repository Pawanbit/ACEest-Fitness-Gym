"""ACEest Fitness & Gym: 
lightweight Flask API for client and progress management."""
import os
import sqlite3
from datetime import date
from flask import Flask, jsonify, request

app = Flask(__name__)
DATABASE = os.environ.get("ACEEST_DATABASE", os.path.join(os.path.dirname(__file__), "aceest_fitness.db"))

PROGRAMS = {
    "Fat Loss (FL)": {"factor": 22, "description": "Fat-loss training plan"},
    "Muscle Gain (MG)": {"factor": 35, "description": "Muscle-gain training plan"},
    "Beginner (BG)": {"factor": 26, "description": "Beginner training plan"},
}

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                age INTEGER NOT NULL CHECK(age > 0),
                height REAL CHECK(height IS NULL OR height > 0),
                weight REAL NOT NULL CHECK(weight > 0),
                program TEXT NOT NULL,
                calories INTEGER NOT NULL,
                target_weight REAL,
                target_adherence INTEGER CHECK(target_adherence IS NULL OR target_adherence BETWEEN 0 AND 100),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
                week TEXT NOT NULL,
                adherence INTEGER NOT NULL CHECK(adherence BETWEEN 0 AND 100),
                notes TEXT DEFAULT ''
            )
        """)

init_db()

def error(message, status):
    return jsonify({"error": message}), status

@app.get("/")
def index():
    return jsonify({
        "application": "ACEest Fitness & Gym",
        "status": "ok",
        "endpoints": ["/health", "/api/programs", "/api/clients", "/api/progress"]
    })

@app.get("/health")
def health():
    return jsonify({"status": "healthy"})

@app.get("/api/programs")
def list_programs():
    return jsonify(PROGRAMS)

@app.get("/api/clients")
def list_clients():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM clients ORDER BY name").fetchall()
    return jsonify([dict(row) for row in rows])

@app.post("/api/clients")
def create_client():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return error("Request body must be a JSON object", 400)
    name = str(data.get("name", "")).strip()
    program = data.get("program")
    if not name:
        return error("name is required", 400)
    if program not in PROGRAMS:
        return error("program must be one of the supported programs", 400)
    try:
        age = int(data.get("age"))
        weight = float(data.get("weight"))
        height = float(data["height"]) if data.get("height") not in (None, "") else None
        target_weight = float(data["target_weight"]) if data.get("target_weight") not in (None, "") else None
        target_adherence = int(data["target_adherence"]) if data.get("target_adherence") not in (None, "") else None
    except (TypeError, ValueError):
        return error("age and weight must be numeric; optional fields must also be numeric", 400)
    if age <= 0 or weight <= 0 or (height is not None and height <= 0):
        return error("age, weight, and height must be positive", 400)
    if target_adherence is not None and not 0 <= target_adherence <= 100:
        return error("target_adherence must be between 0 and 100", 400)
    calories = int(weight * PROGRAMS[program]["factor"])
    try:
        with get_db() as conn:
            cur = conn.execute("""
                INSERT INTO clients (name, age, height, weight, program, calories, target_weight, target_adherence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, age, height, weight, program, calories, target_weight, target_adherence))
            row = conn.execute("SELECT * FROM clients WHERE id = ?", (cur.lastrowid,)).fetchone()
    except sqlite3.IntegrityError:
        return error("A client with this name already exists or the data is invalid", 409)
    return jsonify(dict(row)), 201

@app.get("/api/clients/<int:client_id>")
def get_client(client_id):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()
    if row is None:
        return error("Client not found", 404)
    return jsonify(dict(row))

@app.post("/api/clients/<int:client_id>/progress")
def add_progress(client_id):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return error("Request body must be a JSON object", 400)
    try:
        adherence = int(data.get("adherence"))
    except (TypeError, ValueError):
        return error("adherence must be an integer from 0 to 100", 400)
    if not 0 <= adherence <= 100:
        return error("adherence must be between 0 and 100", 400)
    week = str(data.get("week") or date.today().strftime("Week %U - %Y")).strip()
    notes = str(data.get("notes", "")).strip()
    with get_db() as conn:
        client = conn.execute("SELECT id FROM clients WHERE id = ?", (client_id,)).fetchone()
        if client is None:
            return error("Client not found", 404)
        cur = conn.execute(
            "INSERT INTO progress (client_id, week, adherence, notes) VALUES (?, ?, ?, ?)",
            (client_id, week, adherence, notes),
        )
        row = conn.execute("SELECT * FROM progress WHERE id = ?", (cur.lastrowid,)).fetchone()
    return jsonify(dict(row)), 201

@app.get("/api/clients/<int:client_id>/progress")
def get_progress(client_id):
    with get_db() as conn:
        client = conn.execute("SELECT id FROM clients WHERE id = ?", (client_id,)).fetchone()
        if client is None:
            return error("Client not found", 404)
        rows = conn.execute(
            "SELECT * FROM progress WHERE client_id = ? ORDER BY id", (client_id,)
        ).fetchall()
    return jsonify([dict(row) for row in rows])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
