"""
backend/database.py
---------------------
All interaction with the SQLite database lives here - nowhere else in
the project talks to SQL directly. This keeps a clean separation: the
`logic` layer works with plain Python objects, and only this file knows
the database exists.

Why SQLite?
    - Ships with Python's standard library (`sqlite3`) - nothing extra
      to install.
    - Stores everything in a single file (parking.db) - easy to submit
      alongside the code, no separate database server to set up.
    - Perfectly capable for a single-lot parking system like this one.

Why is this a "DYNAMIC" database (part c of the assignment)?
    - The `tickets` table gains a new row every single time a vehicle
      enters, and that row is updated again when the vehicle exits and
      pays. The number of rows is unknown in advance and keeps growing
      for as long as the car park operates - nothing about its size is
      fixed, which is exactly what "dynamic" means here.
    - The schema also easily extends (e.g. add a `vehicles` table with
      owner details, or a `slots` table with pricing per zone) without
      changing how the rest of the app talks to it.
"""

import os
import sqlite3

# The database file lives at the project root, next to run.py, so it
# survives even if you move the backend/ or logic/ folders around.
DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "parking.db"
)


def get_connection():
    """Open a new connection with rows returned as dict-like objects."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # lets us do row["column_name"]
    return conn


def init_db():
    """
    Create the tickets table if it doesn't already exist. Safe to call
    every time the app starts.

    tickets table (one row per parking "stay"):
        ticket_id     - auto-incrementing primary key
        vehicle_plate - the vehicle's number plate
        slot_id       - which physical slot it was parked in
        entry_time    - ISO timestamp, set on arrival
        exit_time     - ISO timestamp, set on payment/exit (NULL while parked)
        amount_paid   - fee charged (NULL while parked)
        status        - 'ACTIVE' while parked, 'PAID' once settled
    """
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tickets (
            ticket_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_plate TEXT NOT NULL,
            slot_id       INTEGER NOT NULL,
            entry_time    TEXT NOT NULL,
            exit_time     TEXT,
            amount_paid   REAL,
            status        TEXT NOT NULL DEFAULT 'ACTIVE'
        )
        """
    )
    conn.commit()
    conn.close()


def insert_ticket(plate: str, slot_id: int, entry_time: str) -> int:
    """Add a new ACTIVE ticket row when a vehicle enters. Returns its new id."""
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO tickets (vehicle_plate, slot_id, entry_time) VALUES (?, ?, ?)",
        (plate, slot_id, entry_time),
    )
    conn.commit()
    ticket_id = cursor.lastrowid
    conn.close()
    return ticket_id


def close_ticket(ticket_id: int, exit_time: str, amount_paid: float) -> None:
    """Mark a ticket as PAID once the vehicle exits and pays its fee."""
    conn = get_connection()
    conn.execute(
        """
        UPDATE tickets
        SET exit_time = ?, amount_paid = ?, status = 'PAID'
        WHERE ticket_id = ?
        """,
        (exit_time, amount_paid, ticket_id),
    )
    conn.commit()
    conn.close()


def get_active_tickets():
    """Return every ticket that is still ACTIVE (used to restore state on startup)."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM tickets WHERE status = 'ACTIVE'").fetchall()
    conn.close()
    return rows


def get_all_tickets():
    """Return the full parking history, most recent first (for the history page)."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM tickets ORDER BY ticket_id DESC").fetchall()
    conn.close()
    return rows
