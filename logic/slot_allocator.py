"""
logic/slot_allocator.py
------------------------
Implements the ALGORITHM that decides which parking slot a new vehicle
gets, and how a slot is returned to the pool once a vehicle leaves.

Data structure chosen: a MIN-HEAP, using Python's built-in `heapq`.

Why a heap and not just a plain Python list?
  - We always want to hand out the *lowest-numbered* free slot (the one
    closest to the entrance) first.
  - A heap always keeps the smallest item at the front.
  - Reading/removing that smallest item is O(log n); adding a freed
    slot back in is also O(log n).
  - A plain list would force us to sort or scan every slot (O(n)) each
    time someone parks - the heap keeps allocation fast even if the
    car park has hundreds or thousands of bays.
"""

import heapq


class SlotAllocator:
    """Hands out and reclaims parking slot numbers using a min-heap."""

    def __init__(self, total_slots: int):
        """
        Build the heap with every slot marked as free.

        Args:
            total_slots: how many physical bays the car park has.
        """
        # heapq works directly on a plain Python list - heapify()
        # rearranges it in place so it obeys the "min-heap" rule
        # (parent <= its children) in O(n) time, once, up front.
        self._free_slots = list(range(1, total_slots + 1))
        heapq.heapify(self._free_slots)
        self.total_slots = total_slots

    def has_free_slot(self) -> bool:
        """O(1) check: is there anywhere left to park?"""
        return len(self._free_slots) > 0

    def allocate_slot(self) -> int:
        """
        Give out the lowest-numbered free slot.

        Returns:
            The slot id that was allocated.

        Raises:
            ValueError: if the car park is already full.
        """
        if not self.has_free_slot():
            raise ValueError("No free slots available - car park is full.")
        return heapq.heappop(self._free_slots)  # O(log n)

    def release_slot(self, slot_id: int) -> None:
        """
        Return a slot to the pool of available slots once a vehicle exits.

        Args:
            slot_id: the slot that just became free.
        """
        heapq.heappush(self._free_slots, slot_id)  # O(log n)

    def mark_occupied(self, slot_id: int) -> None:
        """
        Remove a specific slot from the free pool without allocating a
        "next" one. Only used once, at startup, when the ParkingLot
        rebuilds its in-memory state from tickets that were already
        active in the database (see parking_lot.py).
        """
        if slot_id in self._free_slots:
            self._free_slots.remove(slot_id)   # O(n), startup-only cost
            heapq.heapify(self._free_slots)    # restore heap order, O(n)

    def free_count(self) -> int:
        """How many slots are currently free (used by the display module)."""
        return len(self._free_slots)
