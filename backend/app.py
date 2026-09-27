"""
backend/app.py
-----------------
The BACKEND: a small Flask web server. Its only job is to:
    1. Receive HTTP requests from the browser (frontend).
    2. Ask the `logic` layer (ParkingLot) to do the actual work.
    3. Render an HTML template (frontend) with the result.

No parking algorithm or data structure lives in this file - all of that
is in logic/. This file is intentionally "thin" so the DSA content
(algorithms + data structures) stays cleanly separated from the web
plumbing.
"""

import os
from flask import Flask, render_template, request, jsonify

from backend import database
from logic.parking_lot import ParkingLot

# --- App + folder setup -----------------------------------------------
# Templates and static files live under ../frontend/ relative to this
# file, so the project keeps a clear frontend / backend / logic split
# on disk, as requested.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = os.path.join(BASE_DIR, "frontend", "templates")
STATIC_DIR = os.path.join(BASE_DIR, "frontend", "static")

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)

# How many physical bays the car park has. Change this one number to
# resize the whole system - everything else adapts automatically.
TOTAL_SLOTS = 10

database.init_db()
parking_lot = ParkingLot(TOTAL_SLOTS)


@app.route("/")
def index():
    """Visual display module: show every slot and its current status."""
    display_data = parking_lot.get_display_data()
    return render_template("index.html", **display_data)


@app.route("/api/slots")
def api_slots():
    """
    JSON version of the same data used by index(). The front-end's
    JavaScript polls this endpoint every few seconds so the slot grid
    can update itself live, without reloading the whole page. The
    logic and data structures are unchanged - this route just serialises
    the same `get_display_data()` result as JSON instead of HTML.
    """
    return jsonify(parking_lot.get_display_data())


@app.route("/entry", methods=["GET", "POST"])
def entry():
    """Vehicle entry module."""
    result = None
    if request.method == "POST":
        plate = request.form.get("plate", "")
        result = parking_lot.park_vehicle(plate)
    return render_template("entry.html", result=result)


@app.route("/exit", methods=["GET", "POST"])
def exit_route():
    """Vehicle exit + billing module."""
    result = None
    if request.method == "POST":
        plate = request.form.get("plate", "")
        result = parking_lot.exit_vehicle(plate)
    return render_template("exit.html", result=result)


@app.route("/history")
def history():
    """Simple read-only view of every ticket ever recorded."""
    tickets = database.get_all_tickets()
    return render_template("history.html", tickets=tickets)
