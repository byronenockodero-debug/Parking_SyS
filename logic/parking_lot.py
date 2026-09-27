"""
logic/parking_lot.py
----------------------
This is the "engine" of the whole system. It ties together the data
structures and algorithms from the other logic modules, and exposes a
simple set of operations that the backend (Flask routes) can call:

    - park_vehicle(plate)
    - exit_vehicle(plate)
    - get_display_data()

DATA STRUCTURES USED HERE, AND WHY:

    1. self.allocator (SlotAllocator -> min-heap)
       Picks/reclaims slot numbers in O(log n). See slot_allocator.py.

    2. self.active_tickets  (dict: plate -> Ticket)
       A hash map gives O(1) average lookup, insert and delete. When a
       car leaves, we need to find its ticket by plate number instantly
       rather than scanning every parked car one by one, which would be
       O(n) with a list.

    3. self.waiting_queue  (collections.deque)
       A FIFO queue for vehicles that arrive while the lot is full.
       deque gives O(1) appends/pops from both ends, unlike a plain
       Python list (which is O(n) to pop from the front). "First come,
       first served" is the fairest policy for a real car park queue.

    4. self.slot_status  (list, indexed by slot_id - 1)
       A simple array is the natural fit for the VISUAL DISPLAY module:
       slot numbers are small, contiguous integers, so a list gives
       O(1) access by index when drawing the grid of slots on the page.
"""

from collections import deque
from datetime import datetime

from logic.slot_allocator import SlotAllocator
from logic.billing import calculate_fee, format_duration
from logic.vehicle import Ticket
from backend import database


def _friendly_timestamp(iso_timestamp: str) -> str:
    """Turn '2026-09-26T14:32:07' into '26 Sep 2026, 14:32:07' for display."""
    return datetime.fromisoformat(iso_timestamp).strftime("%d %b %Y, %H:%M:%S")


class ParkingLot:
    """The single in-memory 'brain' of the car park, backed by SQLite."""

    def __init__(self, total_slots: int):
        self.total_slots = total_slots
        self.allocator = SlotAllocator(total_slots)

        # slot_status[i] holds either None (free) or the plate parked
        # in slot (i + 1). Kept purely so the display module can render
        # the grid without touching the database on every page load.
        self.slot_status = [None] * total_slots

        self.active_tickets = {}     # plate -> Ticket
        self.waiting_queue = deque()  # plates waiting for a free slot

        self._restore_state_from_database()

    # ------------------------------------------------------------------
    # Startup / persistence
    # ------------------------------------------------------------------
    def _restore_state_from_database(self):
        """
        On startup, rebuild the in-memory structures from the database
        so a server restart doesn't lose track of who is currently
        parked.

        This is exactly why the database is described as "dynamic" in
        the assignment: it grows and changes with every entry/exit, and
        the in-memory structures above are just a fast working copy of
        whatever the database already knows.
        """
        for row in database.get_active_tickets():
            ticket = Ticket(
                ticket_id=row["ticket_id"],
                plate=row["vehicle_plate"],
                slot_id=row["slot_id"],
                entry_time=row["entry_time"],
            )
            self.active_tickets[ticket.plate] = ticket
            self.slot_status[ticket.slot_id - 1] = ticket.plate
            self.allocator.mark_occupied(ticket.slot_id)

    # ------------------------------------------------------------------
    # Module: Vehicle Entry
    # ------------------------------------------------------------------
    def park_vehicle(self, plate: str) -> dict:
        """
        Algorithm (Vehicle Entry module):
            1. Reject duplicate plates that are already parked.
            2. If a slot is free, allocate it and create + store a ticket.
            3. If the lot is full, push the plate onto the waiting queue
               instead, so it is served the moment a slot frees up.

        Returns a small status dict the Flask route can show the user.
        """
        plate = plate.strip().upper()
        if not plate:
            return {"success": False, "message": "Please enter a number plate."}

        if plate in self.active_tickets:
            return {"success": False, "message": f"{plate} is already parked."}

        if not self.allocator.has_free_slot():
            self.waiting_queue.append(plate)
            return {
                "success": False,
                "message": "Car park is full. You have been added to the waiting queue.",
                "queue_position": len(self.waiting_queue),
            }

        slot_id = self.allocator.allocate_slot()
        entry_time = datetime.now().isoformat(timespec="seconds")

        ticket_id = database.insert_ticket(plate, slot_id, entry_time)
        ticket = Ticket(ticket_id, plate, slot_id, entry_time)

        self.active_tickets[plate] = ticket
        self.slot_status[slot_id - 1] = plate

        return {
            "success": True,
            "message": f"Welcome. Slot {slot_id} assigned.",
            "slot_id": slot_id,
            "entry_time_display": _friendly_timestamp(entry_time),
        }

    # ------------------------------------------------------------------
    # Module: Vehicle Exit & Billing
    # ------------------------------------------------------------------
    def exit_vehicle(self, plate: str) -> dict:
        """
        Algorithm (Exit + Billing module):
            1. Look up the ticket by plate (O(1) via the hash map).
            2. Calculate the fee using the billing algorithm.
            3. Persist the exit + payment in the database.
            4. Free the slot and "open the barrier" (simulated by the
               success message - a real barrier controller would be
               triggered at this exact point).
            5. If anyone is waiting in the queue, immediately allocate
               the now-free slot to the next car in line (FIFO).
        """
        plate = plate.strip().upper()
        ticket = self.active_tickets.get(plate)

        if ticket is None:
            return {"success": False, "message": f"No active ticket found for {plate}."}

        exit_time = datetime.now().isoformat(timespec="seconds")
        fee = calculate_fee(ticket.entry_time, exit_time)
        duration_text = format_duration(ticket.entry_time, exit_time)

        database.close_ticket(ticket.ticket_id, exit_time, fee)

        freed_slot = ticket.slot_id
        del self.active_tickets[plate]
        self.slot_status[freed_slot - 1] = None
        self.allocator.release_slot(freed_slot)

        result = {
            "success": True,
            "message": f"Payment received (KES {fee:.2f}). Barrier open - drive safely!",
            "amount_paid": fee,
            "plate": plate,
            "slot_id": freed_slot,
            # Real, unrounded elapsed time (e.g. "3 minutes") - kept
            # separate from the billing fee above, which rounds
            # partial hours up for pricing purposes only.
            "duration_text": duration_text,
            "entry_time_display": _friendly_timestamp(ticket.entry_time),
            "exit_time_display": _friendly_timestamp(exit_time),
        }

        # Serve the next waiting vehicle, if any (FIFO queue).
        if self.waiting_queue:
            next_plate = self.waiting_queue.popleft()
            served = self.park_vehicle(next_plate)
            result["next_served"] = next_plate if served["success"] else None

        return result

    # ------------------------------------------------------------------
    # Module: Visual Display
    # ------------------------------------------------------------------
    def get_display_data(self) -> dict:
        """
        Algorithm (Display module):
            Walk the slot_status array (O(n), where n is the small
            number of physical slots) and report free/occupied for
            each one, plus overall totals for the page header.
        """
        slots = [
            {"slot_id": i + 1, "occupied": plate is not None, "plate": plate}
            for i, plate in enumerate(self.slot_status)
        ]
        return {
            "slots": slots,
            "free_count": self.allocator.free_count(),
            "total_slots": self.total_slots,
            "waiting_count": len(self.waiting_queue),
        }
