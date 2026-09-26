"""Unit tests for Hotel Conference Hall Booking & Catering Package Pricing Engine (CR-805)."""

from datetime import date, time
import pytest

from booking.conference_pricing import (
    ConferenceBooking,
    ConferenceHall,
    ConferenceHallPricingEngine,
    DEFAULT_CATERING_RATE_PER_HEAD,
)


@pytest.fixture
def engine():
    return ConferenceHallPricingEngine(default_catering_rate=35.0)


@pytest.fixture
def standard_hall():
    return ConferenceHall(
        hall_id="HALL-GRAND-1",
        name="Grand Ballroom",
        capacity=150,
        base_rental_rate=1200.0,
    )


def test_calculates_conference_event_cost_formula(engine):
    """Calculates conference event cost: hall_rate + (attendee_count * catering_rate) + equipment_fee."""
    # hall_rate=1200.0, attendee_count=60, catering_rate=35.0, equipment_fee=300.0
    # catering_cost = 60 * 35.0 = 2100.0
    # total_cost = 1200.0 + 2100.0 + 300.0 = 3600.0
    cost = engine.calculate_event_cost(
        hall_rate=1200.0,
        attendee_count=60,
        catering_rate=35.0,
        equipment_fee=300.0,
    )

    assert cost["hall_rental"] == 1200.0
    assert cost["catering_cost"] == 2100.0
    assert cost["av_equipment_fee"] == 300.0
    assert cost["total_cost"] == 3600.0


def test_default_catering_rate_thirty_five_per_head(engine):
    """Defaults to $35/head standard catering package when catering_rate is None."""
    cost = engine.calculate_event_cost(
        hall_rate=800.0,
        attendee_count=40,
        catering_rate=None,
        equipment_fee=150.0,
    )

    # 40 * $35 = 1400.0 catering cost
    assert cost["catering_cost"] == 1400.0
    assert cost["total_cost"] == 800.0 + 1400.0 + 150.0  # 2350.0


def test_zero_attendees_and_zero_equipment_fee(engine):
    """Event with only hall rental fee."""
    cost = engine.calculate_event_cost(
        hall_rate=500.0,
        attendee_count=0,
        equipment_fee=0.0,
    )
    assert cost["hall_rental"] == 500.0
    assert cost["catering_cost"] == 0.0
    assert cost["av_equipment_fee"] == 0.0
    assert cost["total_cost"] == 500.0


def test_check_availability_no_conflict(engine, standard_hall):
    """Available when no existing reservations are on the calendar."""
    is_available = engine.check_availability(
        hall_id=standard_hall.hall_id,
        event_date=date(2026, 10, 15),
        start_time=time(9, 0),
        end_time=time(13, 0),
    )
    assert is_available is True


def test_check_availability_double_booking_conflict(engine, standard_hall):
    """Detects overlapping reservation on the same date and hall."""
    engine.create_booking(
        hall=standard_hall,
        client_name="Acme Corp",
        event_date=date(2026, 10, 15),
        start_time=time(10, 0),
        end_time=time(14, 0),
        attendee_count=50,
        av_equipment_fee=200.0,
    )

    # Overlapping case 1: Completely inside (11:00 to 13:00)
    assert engine.check_availability(
        hall_id=standard_hall.hall_id,
        event_date=date(2026, 10, 15),
        start_time=time(11, 0),
        end_time=time(13, 0),
    ) is False

    # Overlapping case 2: Starts earlier, ends inside (09:00 to 11:00)
    assert engine.check_availability(
        hall_id=standard_hall.hall_id,
        event_date=date(2026, 10, 15),
        start_time=time(9, 0),
        end_time=time(11, 0),
    ) is False

    # Overlapping case 3: Enclosing (08:00 to 16:00)
    assert engine.check_availability(
        hall_id=standard_hall.hall_id,
        event_date=date(2026, 10, 15),
        start_time=time(8, 0),
        end_time=time(16, 0),
    ) is False


def test_adjacent_time_slots_do_not_conflict(engine, standard_hall):
    """Consecutive non-overlapping slots (touching boundaries) do not collide."""
    engine.create_booking(
        hall=standard_hall,
        client_name="Morning Conference",
        event_date=date(2026, 10, 20),
        start_time=time(9, 0),
        end_time=time(12, 0),
        attendee_count=40,
    )

    # Afternoon slot starting exactly when morning slot ends (12:00 to 15:00)
    assert engine.check_availability(
        hall_id=standard_hall.hall_id,
        event_date=date(2026, 10, 20),
        start_time=time(12, 0),
        end_time=time(15, 0),
    ) is True

    # Early morning slot ending exactly when morning slot starts (07:00 to 09:00)
    assert engine.check_availability(
        hall_id=standard_hall.hall_id,
        event_date=date(2026, 10, 20),
        start_time=time(7, 0),
        end_time=time(9, 0),
    ) is True


def test_different_halls_same_time_no_conflict(engine, standard_hall):
    """Separate halls can be booked simultaneously without conflict."""
    second_hall = ConferenceHall(
        hall_id="HALL-CEDAR-2",
        name="Cedar Room",
        capacity=50,
        base_rental_rate=600.0,
    )

    engine.create_booking(
        hall=standard_hall,
        client_name="Hall 1 Client",
        event_date=date(2026, 11, 1),
        start_time=time(10, 0),
        end_time=time(16, 0),
        attendee_count=50,
    )

    assert engine.check_availability(
        hall_id=second_hall.hall_id,
        event_date=date(2026, 11, 1),
        start_time=time(10, 0),
        end_time=time(16, 0),
    ) is True


def test_booking_exceeding_capacity_raises_error(engine, standard_hall):
    """Attempting to book more attendees than hall capacity raises ValueError."""
    with pytest.raises(ValueError, match="exceeds hall capacity"):
        engine.create_booking(
            hall=standard_hall,  # capacity = 150
            client_name="Massive Summit",
            event_date=date(2026, 11, 5),
            start_time=time(9, 0),
            end_time=time(17, 0),
            attendee_count=200,
        )


def test_double_booking_creation_raises_error(engine, standard_hall):
    """Attempting to create an overlapping booking raises ValueError."""
    engine.create_booking(
        hall=standard_hall,
        client_name="First Org",
        event_date=date(2026, 12, 1),
        start_time=time(10, 0),
        end_time=time(14, 0),
        attendee_count=80,
    )

    with pytest.raises(ValueError, match="Double-booking conflict"):
        engine.create_booking(
            hall=standard_hall,
            client_name="Second Org",
            event_date=date(2026, 12, 1),
            start_time=time(12, 0),
            end_time=time(16, 0),
            attendee_count=50,
        )


def test_invalid_parameters_validation(engine):
    """Rejects negative costs, negative attendees, or inverted time slots."""
    with pytest.raises(ValueError, match="hall_rate cannot be negative"):
        engine.calculate_event_cost(hall_rate=-100.0, attendee_count=10)

    with pytest.raises(ValueError, match="attendee_count cannot be negative"):
        engine.calculate_event_cost(hall_rate=500.0, attendee_count=-5)

    with pytest.raises(ValueError, match="equipment_fee cannot be negative"):
        engine.calculate_event_cost(hall_rate=500.0, attendee_count=10, equipment_fee=-50.0)

    with pytest.raises(ValueError, match="start_time must be earlier than end_time"):
        engine.check_availability("H-1", date(2026, 1, 1), time(15, 0), time(10, 0))
