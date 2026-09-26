"""Hotel Conference Hall Booking & Catering Package Pricing Engine (CR-805).

Calculates conference event costs: hall_rate + (attendee_count * catering_rate) + equipment_fee,
verifies hall date/time calendar availability to prevent double-booking conflicts,
and manages event reservations with customizable AV equipment rental tiers and catering packages.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, time, timezone
from typing import Any, Dict, List, Optional
import uuid


DEFAULT_CATERING_RATE_PER_HEAD: float = 35.0  # $35/head standard package


@dataclass
class ConferenceHall:
    """Represents a banquet or conference hall venue."""
    hall_id: str
    name: str
    capacity: int
    base_rental_rate: float
    is_active: bool = True

    def __post_init__(self):
        self.hall_id = self.hall_id.strip()
        self.name = self.name.strip()
        if self.capacity <= 0:
            raise ValueError(f"Hall capacity must be positive, got {self.capacity}")
        if self.base_rental_rate < 0:
            raise ValueError(f"Base rental rate cannot be negative, got {self.base_rental_rate}")


@dataclass
class ConferenceBooking:
    """Represents a confirmed conference hall reservation."""
    booking_id: str
    hall_id: str
    client_name: str
    event_date: date
    start_time: time
    end_time: time
    attendee_count: int
    catering_rate_per_head: float
    av_equipment_fee: float
    hall_rental: float
    catering_cost: float
    total_cost: float
    status: str = "Confirmed"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "booking_id": self.booking_id,
            "hall_id": self.hall_id,
            "client_name": self.client_name,
            "event_date": self.event_date.isoformat(),
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "attendee_count": self.attendee_count,
            "catering_rate_per_head": self.catering_rate_per_head,
            "av_equipment_fee": self.av_equipment_fee,
            "hall_rental": self.hall_rental,
            "catering_cost": self.catering_cost,
            "total_cost": self.total_cost,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
        }


class ConferenceHallPricingEngine:
    """Engine computing conference hall package pricing and calendar collision prevention."""

    def __init__(self, default_catering_rate: float = DEFAULT_CATERING_RATE_PER_HEAD):
        self.default_catering_rate = float(default_catering_rate)
        self._bookings: List[ConferenceBooking] = []

    def calculate_event_cost(
        self,
        hall_rate: float,
        attendee_count: int,
        catering_rate: Optional[float] = None,
        equipment_fee: float = 0.0,
    ) -> Dict[str, float]:
        """Calculate conference event cost: hall_rate + (attendee_count * catering_rate) + equipment_fee.

        Acceptance criterion:
        Calculates conference event cost: hall_rate + (attendee_count * catering_rate) + equipment_fee.
        """
        if hall_rate < 0:
            raise ValueError(f"hall_rate cannot be negative, got {hall_rate}")
        if attendee_count < 0:
            raise ValueError(f"attendee_count cannot be negative, got {attendee_count}")
        if equipment_fee < 0:
            raise ValueError(f"equipment_fee cannot be negative, got {equipment_fee}")

        rate = self.default_catering_rate if catering_rate is None else float(catering_rate)
        if rate < 0:
            raise ValueError(f"catering_rate cannot be negative, got {rate}")

        catering_cost = round(attendee_count * rate, 2)
        total_cost = round(float(hall_rate) + catering_cost + float(equipment_fee), 2)

        return {
            "hall_rental": round(float(hall_rate), 2),
            "catering_cost": catering_cost,
            "av_equipment_fee": round(float(equipment_fee), 2),
            "total_cost": total_cost,
        }

    def check_availability(
        self,
        hall_id: str,
        event_date: date,
        start_time: time,
        end_time: time,
        booking_list: Optional[List[ConferenceBooking]] = None,
    ) -> bool:
        """Check hall date/time availability to prevent double-booking.

        Two reservations overlap if they share the same hall and date, and:
        start_time < existing.end_time and end_time > existing.start_time.
        """
        if start_time >= end_time:
            raise ValueError("start_time must be earlier than end_time")

        active_bookings = self._bookings if booking_list is None else booking_list

        for b in active_bookings:
            if b.hall_id == hall_id and b.event_date == event_date and b.status != "Cancelled":
                # Overlap check: max(start1, start2) < min(end1, end2)
                if start_time < b.end_time and end_time > b.start_time:
                    return False

        return True

    def create_booking(
        self,
        hall: ConferenceHall,
        client_name: str,
        event_date: date,
        start_time: time,
        end_time: time,
        attendee_count: int,
        catering_rate: Optional[float] = None,
        av_equipment_fee: float = 0.0,
    ) -> ConferenceBooking:
        """Reserve a conference hall after validating capacity and scheduling conflicts."""
        client_name = client_name.strip()
        if not client_name:
            raise ValueError("Client name cannot be empty.")
        if attendee_count > hall.capacity:
            raise ValueError(
                f"Attendee count ({attendee_count}) exceeds hall capacity ({hall.capacity})."
            )

        if not self.check_availability(hall.hall_id, event_date, start_time, end_time):
            raise ValueError(
                f"Double-booking conflict: Hall '{hall.hall_id}' is already booked on "
                f"{event_date.isoformat()} between {start_time.isoformat()} and {end_time.isoformat()}."
            )

        rate = self.default_catering_rate if catering_rate is None else catering_rate
        cost_breakdown = self.calculate_event_cost(
            hall_rate=hall.base_rental_rate,
            attendee_count=attendee_count,
            catering_rate=rate,
            equipment_fee=av_equipment_fee,
        )

        booking = ConferenceBooking(
            booking_id=f"CONF-{uuid.uuid4().hex[:8].upper()}",
            hall_id=hall.hall_id,
            client_name=client_name,
            event_date=event_date,
            start_time=start_time,
            end_time=end_time,
            attendee_count=attendee_count,
            catering_rate_per_head=rate,
            av_equipment_fee=cost_breakdown["av_equipment_fee"],
            hall_rental=cost_breakdown["hall_rental"],
            catering_cost=cost_breakdown["catering_cost"],
            total_cost=cost_breakdown["total_cost"],
            status="Confirmed",
        )

        self._bookings.append(booking)
        return booking

    def get_bookings(self, hall_id: Optional[str] = None) -> List[ConferenceBooking]:
        """Retrieve confirmed bookings, optionally filtered by hall ID."""
        if hall_id:
            return [b for b in self._bookings if b.hall_id == hall_id]
        return list(self._bookings)
