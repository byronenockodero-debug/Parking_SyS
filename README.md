# Smart Parking System (DSA Task One)

A small web-based parking system: drivers see a live visual display of
free/occupied slots, the system records vehicles on arrival, and
automatically calculates the fee and "opens the barrier" on exit.

Built entirely in Python (Flask + SQLite) with plain HTML/CSS on the
front end, so no other language is required to read or extend it.

## Project structure

```
parking_system/
├── run.py                   # Start here: `python run.py`
├── requirements.txt          # One dependency: Flask
├── backend/                  # BACKEND - the web server
│   ├── app.py                 # Flask routes (thin - no algorithms here)
│   └── database.py            # All SQL lives here (SQLite)
├── logic/                    # LOGIC - data structures & algorithms
│   ├── vehicle.py             # Ticket data model
│   ├── slot_allocator.py      # Slot allocation algorithm (min-heap)
│   ├── billing.py             # Fee calculation algorithm
│   └── parking_lot.py         # Ties the above together (the "engine")
└── frontend/                 # FRONTEND - what the browser renders
    ├── templates/              # HTML pages (Jinja2)
    └── static/
        ├── css/style.css       # Styling
        └── js/script.js        # Tiny, optional cosmetic script
```

The split is deliberate: `backend/` only knows how to receive requests
and talk to the database; `logic/` only knows Python data structures
and algorithms; `frontend/` only knows HTML/CSS. You can read, mark, or
extend any one of them without touching the others.

## How to run it locally

```bash
# 1. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows (PowerShell)
source venv/bin/activate     # macOS / Linux

# 2. Install the one dependency
pip install -r requirements.txt

# 3. Run the server
python run.py
```

Then open **http://127.0.0.1:5000** in your browser. A `parking.db`
SQLite file is created automatically the first time you run it.

## The assignment's three parts, answered in code

**a) Algorithm for each module** - each module is its own file with a
docstring explaining its algorithm step by step:
- Vehicle Entry: `ParkingLot.park_vehicle()` in `logic/parking_lot.py`
- Slot Allocation: `logic/slot_allocator.py`
- Exit & Billing: `ParkingLot.exit_vehicle()` + `logic/billing.py`
- Visual Display: `ParkingLot.get_display_data()`

**b) Data structures and reasons for their use**
| Structure | Where | Why |
|---|---|---|
| Min-heap (`heapq`) | `slot_allocator.py` | Always hand out the lowest free slot number in O(log n), instead of scanning/sorting in O(n). |
| Hash map (`dict`) | `active_tickets` in `parking_lot.py` | O(1) average lookup of a parked car by plate number when it exits. |
| Queue (`collections.deque`) | `waiting_queue` in `parking_lot.py` | O(1) FIFO queue for vehicles that arrive when the lot is full - fairest real-world policy. |
| Array (`list`) | `slot_status` in `parking_lot.py` | O(1) indexed access for rendering the slot grid on the display page. |

**c) Dynamic database design** - see `backend/database.py`. One table,
`tickets`, grows by a row on every entry and is updated on every exit,
so its size and content are never fixed in advance:

```
tickets
-------
ticket_id      INTEGER PRIMARY KEY AUTOINCREMENT
vehicle_plate  TEXT
slot_id        INTEGER
entry_time     TEXT (ISO timestamp)
exit_time      TEXT (ISO timestamp, NULL while parked)
amount_paid    REAL (NULL while parked)
status         TEXT  ('ACTIVE' or 'PAID')
```

On startup, `ParkingLot._restore_state_from_database()` reloads every
`ACTIVE` ticket, so a server restart never loses track of who is
currently parked - the database is the durable source of truth, and
the in-memory structures above are just a fast working copy of it.

## Deploying it so others can see a live link (optional)

The assignment only asks for a GitHub submission, so this step is
optional - but if you want a clickable live demo like some GitHub repos
have:

- Push the code to GitHub as-is (the `.gitignore` already excludes
  `venv/` and `parking.db`).
- Connect the repo to a free host that keeps a Python process running,
  e.g. **Render.com** or **PythonAnywhere** (both have beginner-friendly
  free tiers for Flask apps).
- Set the start command to `python run.py` (with `debug=False`), and
  the host gives you a public URL - no venv or local setup needed by
  anyone who visits it.
