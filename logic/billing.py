"""
logic/billing.py
-----------------
The ALGORITHM that turns "how long was the vehicle parked" into
"how much do they owe".

This module holds no data structures of its own - it's pure
calculation - but it is kept in its own file, separate from
parking_lot.py, so the *pricing policy* can be changed independently
of the *tracking/allocation logic*.
"""

import math
from datetime import datetime

# --- Pricing policy ---------------------------------------------------
# Edit these two numbers to match the client's real rate card.
FIRST_HOUR_RATE = 50    # KES for the first hour, or any part of it
EXTRA_HOUR_RATE = 30    # KES for every additional hour, or any part of it


def calculate_fee(entry_time: str, exit_time: str) -> float:
    """
    Work out the parking fee for a single stay.

    Args:
        entry_time: ISO-format timestamp string, e.g. "2026-09-26T10:15:00".
        exit_time:  ISO-format timestamp string for when the vehicle left.

    Returns:
        The fee in KES, as a float.

    Algorithm:
        1. Parse both timestamps into datetime objects.
        2. Find the elapsed time and convert it to hours.
        3. Round PARTIAL hours UP (math.ceil) - a car parked for 61
           minutes is billed for 2 hours, not 1.02 hours. This is
           standard practice for real parking systems.
        4. The first hour is billed at FIRST_HOUR_RATE, every hour
           after that at EXTRA_HOUR_RATE.
    """
    entry_dt = datetime.fromisoformat(entry_time)
    exit_dt = datetime.fromisoformat(exit_time)

    elapsed_seconds = (exit_dt - entry_dt).total_seconds()
    if elapsed_seconds < 0:
        raise ValueError("Exit time cannot be before entry time.")

    # Always charge at least 1 hour, and round any partial hour up.
    hours = max(1, math.ceil(elapsed_seconds / 3600))

    if hours <= 1:
        return float(FIRST_HOUR_RATE)

    extra_hours = hours - 1
    return float(FIRST_HOUR_RATE + extra_hours * EXTRA_HOUR_RATE)


def format_duration(entry_time: str, exit_time: str) -> str:
    """
    Turn the *exact* elapsed time into a human-readable string, e.g.
    "3 minutes" or "1 hour 12 minutes".

    This is deliberately separate from calculate_fee() above: billing
    rounds partial hours UP because that's how the fee is charged, but
    the time actually shown to the driver should reflect real life -
    if they were parked for 3 minutes, the display should say
    "3 minutes", not "1 hour" just because that's the billing bracket.

    Args:
        entry_time: ISO-format timestamp string.
        exit_time:  ISO-format timestamp string.

    Returns:
        A short string such as "45 seconds", "3 minutes", or
        "1 hour 12 minutes".
    """
    entry_dt = datetime.fromisoformat(entry_time)
    exit_dt = datetime.fromisoformat(exit_time)

    total_seconds = int((exit_dt - entry_dt).total_seconds())
    if total_seconds < 0:
        raise ValueError("Exit time cannot be before entry time.")

    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts = []
    if hours:
        parts.append(f"{hours} hour" + ("s" if hours != 1 else ""))
    if minutes:
        parts.append(f"{minutes} minute" + ("s" if minutes != 1 else ""))
    if not hours and not minutes:
        # Very short stay (under a minute) - show seconds so it still
        # reads as accurate, instead of rounding down to "0 minutes".
        parts.append(f"{seconds} second" + ("s" if seconds != 1 else ""))

    return " ".join(parts)
