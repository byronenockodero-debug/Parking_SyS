"""
logic/vehicle.py
-----------------
Defines the data container that represents one vehicle's parking ticket.

We use a Python `dataclass` here instead of a plain dictionary because:
  - It gives every ticket a clear, fixed shape (self-documenting fields).
  - It still behaves like a normal Python object (dot-notation access,
    e.g. `ticket.plate` instead of `ticket["plate"]`).
  - It needs no extra library - dataclasses are in the standard library.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Ticket:
    """
    Represents one "stay" of a vehicle inside the parking lot.

    Attributes:
        ticket_id (int): Unique id for this ticket (matches its database row).
        plate (str): The vehicle's number plate - used as the lookup key
                      in the active_tickets hash map (see parking_lot.py).
        slot_id (int): Which physical slot the vehicle was assigned to.
        entry_time (str): ISO-format timestamp of when the vehicle arrived.
        exit_time (Optional[str]): ISO-format timestamp of when it left
                                    (stays None while the vehicle is parked).
        amount_paid (Optional[float]): Fee charged at exit (None while parked).
    """
    ticket_id: int
    plate: str
    slot_id: int
    entry_time: str
    exit_time: Optional[str] = None
    amount_paid: Optional[float] = None
