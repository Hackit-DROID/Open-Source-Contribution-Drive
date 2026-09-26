"""Unit tests for Student Hostel Check-Out Clearance & Security Deposit Refund Ledger (CR-803)."""

from unittest.mock import MagicMock
import pytest

from hostel.clearance_engine import (
    ClearanceCertificate,
    DamageAssessment,
    HostelCheckOutClearanceEngine,
)


@pytest.fixture
def engine():
    return HostelCheckOutClearanceEngine()


def test_compute_net_refund_standard(engine):
    """Computes net security deposit refund: max(0, deposit - (mess_due + damage_fee))."""
    # 500 deposit - (120 mess + 80 damage) = 300 net refund
    refund = engine.compute_net_refund(
        initial_deposit=500.0,
        unpaid_mess_bills=120.0,
        room_damage_fees=80.0,
    )
    assert refund == 300.0


def test_compute_net_refund_zero_when_deductions_exceed_deposit(engine):
    """Net refund clamped to 0.0 when deductions exceed initial deposit."""
    # 500 deposit - (400 mess + 250 damage) = 0 net refund
    refund = engine.compute_net_refund(
        initial_deposit=500.0,
        unpaid_mess_bills=400.0,
        room_damage_fees=250.0,
    )
    assert refund == 0.0


def test_full_refund_when_no_deductions(engine):
    """Returns 100% of initial deposit if student has zero unpaid dues or damages."""
    refund = engine.compute_net_refund(
        initial_deposit=750.0,
        unpaid_mess_bills=0.0,
        room_damage_fees=0.0,
    )
    assert refund == 750.0


def test_audits_unpaid_mess_bills_and_room_damage_assessment_fees(engine):
    """Audits unpaid mess bills and itemized damage assessment fees."""
    damages = [
        DamageAssessment("DMG-01", "Broken window latch", 35.50, "Warden John"),
        DamageAssessment("DMG-02", "Wall repaint requirement", 64.50, "Warden John"),
    ]

    cert = engine.process_checkout_clearance(
        student_name="Alice Smith",
        room_no="B-204",
        initial_deposit=600.0,
        unpaid_mess_bills=150.0,
        damage_assessments=damages,
    )

    assert cert.initial_deposit == 600.0
    assert cert.unpaid_mess_bills == 150.0
    assert cert.room_damage_fees == 100.0  # 35.50 + 64.50
    assert cert.total_deductions == 250.0  # 150.0 + 100.0
    assert cert.net_refund == 350.0        # 600.0 - 250.0
    assert cert.has_outstanding_liability is False
    assert cert.outstanding_liability_amount == 0.0
    assert len(cert.damage_items) == 2


def test_updates_student_hostel_allocation_status_to_checked_out(engine):
    """Updates student hostel allocation status to 'Checked Out'."""
    mock_hostel = MagicMock()
    mock_hostel.status = "Occupied"
    mock_hostel.student_name = "Bob Miller"
    mock_hostel.room_no = "C-101"

    cert = engine.process_checkout_clearance(
        student_name=mock_hostel.student_name,
        room_no=mock_hostel.room_no,
        initial_deposit=500.0,
        unpaid_mess_bills=50.0,
        hostel_record=mock_hostel,
    )

    assert mock_hostel.status == "Checked Out"
    mock_hostel.save.assert_called_once()
    assert cert.status == "Checked Out"


def test_outstanding_liability_flagged_when_deductions_exceed_deposit(engine):
    """Flags outstanding liability when damages and mess bills exceed deposit."""
    damages = [
        DamageAssessment("DMG-03", "Mattress destruction", 200.0),
        DamageAssessment("DMG-04", "Door replacement", 350.0),
    ]

    cert = engine.process_checkout_clearance(
        student_name="Charlie Brown",
        room_no="A-105",
        initial_deposit=400.0,
        unpaid_mess_bills=200.0,
        damage_assessments=damages,
    )

    # Total deductions: 200 mess + 550 damages = 750. Deposit = 400.
    assert cert.total_deductions == 750.0
    assert cert.net_refund == 0.0
    assert cert.has_outstanding_liability is True
    assert cert.outstanding_liability_amount == 350.0  # 750 - 400


def test_certificate_to_dict_structure(engine):
    """Certificate serializes cleanly to dictionary for JSON API responses."""
    cert = engine.process_checkout_clearance(
        student_name="Diana Prince",
        room_no="D-401",
        initial_deposit=500.0,
        unpaid_mess_bills=50.0,
    )

    d = cert.to_dict()
    assert d["student_name"] == "Diana Prince"
    assert d["room_no"] == "D-401"
    assert d["status"] == "Checked Out"
    assert d["net_refund"] == 450.0
    assert "certificate_id" in d
    assert "cleared_at" in d


def test_input_validation(engine):
    """Rejects empty student name, empty room number, or negative fees."""
    with pytest.raises(ValueError, match="Student name cannot be empty"):
        engine.process_checkout_clearance("", "101", 500.0)

    with pytest.raises(ValueError, match="Room number cannot be empty"):
        engine.process_checkout_clearance("Dave", "", 500.0)

    with pytest.raises(ValueError, match="Initial deposit cannot be negative"):
        engine.compute_net_refund(-100.0, 0.0, 0.0)

    with pytest.raises(ValueError, match="Unpaid mess bills cannot be negative"):
        engine.compute_net_refund(500.0, -50.0, 0.0)

    with pytest.raises(ValueError, match="Damage fee cannot be negative"):
        DamageAssessment("D-ERR", "Test", -20.0)
