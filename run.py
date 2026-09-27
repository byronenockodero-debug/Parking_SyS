"""
run.py
--------
Single entry point that starts the whole system.

Usage:
    python run.py

This just imports the Flask `app` object from backend/app.py and starts
the built-in development server. Keeping this file at the project root
means the two internal packages (`backend` and `logic`) can import each
other cleanly using plain package names, e.g. `from logic.parking_lot
import ParkingLot`.
"""

from backend.app import app

if __name__ == "__main__":
    # debug=True auto-reloads the server whenever you edit code, and
    # shows readable error pages while you're developing. Turn it off
    # (debug=False) before deploying anywhere public.
    app.run(debug=True)
