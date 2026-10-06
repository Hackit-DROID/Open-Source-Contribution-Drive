"""Unit tests for Blood Inventory Expiry Audit & Automated Stock Reclamation Workflow (CR-616)."""

import os
import sys
from datetime import date, timedelta
import pytest

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from inventory.reclamation_workflow import (
    BloodInventoryReclamationEngine,
    BloodStockItem,
    DisposalAuditRecord,
    DEFAULT_STORAGE_THRESHOLD_DAYS,
)


@pytest.fixture
def engine():
    """Returns a freshly initialized BloodInventoryReclamationEngine."""
    return BloodInventoryReclamationEngine(storage_threshold_days=42)


@pytest.fixture
def today():
    return date(2026, 10, 6)


def test_blood_stock_item_age_and_expiry(today):
    """Verifies age calculation and expiry check against 42-day threshold."""
    # 30-day-old unit -> Active, not expired
    fresh_unit = BloodStockItem(
        sample_id="SAMPLE-001",
        blood_group="A+",
        units=5,
        donated_date=today - timedelta(days=30),
    )
    assert fresh_unit.get_age_days(reference_date=today) == 30
    assert not fresh_unit.is_expired(reference_date=today)

    # 45-day-old unit -> Expired (> 42 days)
    expired_unit = BloodStockItem(
        sample_id="SAMPLE-002",
        blood_group="O-",
        units=3,
        donated_date=today - timedelta(days=45),
    )
    assert expired_unit.get_age_days(reference_date=today) == 45
    assert expired_unit.is_expired(reference_date=today)


def test_threshold_boundary_conditions(today):
    """Verifies exact 42-day threshold boundary behavior."""
    # Exactly 42 days old -> not yet expired (> 42 threshold)
    unit_42 = BloodStockItem(
        sample_id="SAMPLE-042",
        blood_group="B+",
        units=2,
        donated_date=today - timedelta(days=42),
    )
    assert not unit_42.is_expired(reference_date=today, threshold_days=42)

    # 43 days old -> expired
    unit_43 = BloodStockItem(
        sample_id="SAMPLE-043",
        blood_group="B+",
        units=2,
        donated_date=today - timedelta(days=43),
    )
    assert unit_43.is_expired(reference_date=today, threshold_days=42)


def test_identifies_expired_stock_units(engine, today):
    """Verifies scanner identifies all units exceeding the 42-day storage threshold."""
    engine.add_stock_unit(
        sample_id="UNIT-FRESH-1",
        blood_group="O+",
        units=10,
        donated_date=today - timedelta(days=15),
    )
    engine.add_stock_unit(
        sample_id="UNIT-EXP-1",
        blood_group="O+",
        units=4,
        donated_date=today - timedelta(days=50),
    )
    engine.add_stock_unit(
        sample_id="UNIT-EXP-2",
        blood_group="AB-",
        units=6,
        donated_date=today - timedelta(days=60),
    )

    result = engine.scan_and_reclaim_expired_stock(reference_date=today)

    assert result["scanned_samples"] == 3
    assert result["expired_samples_count"] == 2
    assert result["total_units_reclaimed"] == 10  # 4 + 6
    assert result["status"] == "COMPLETED"


def test_deducts_expired_units_and_marks_disposed(engine, today):
    """Verifies expired units are deducted from active stock and marked 'Disposed'."""
    engine.add_stock_unit(
        sample_id="BATCH-001",
        blood_group="A+",
        units=8,
        donated_date=today - timedelta(days=10),
    )
    engine.add_stock_unit(
        sample_id="BATCH-002",
        blood_group="A+",
        units=5,
        donated_date=today - timedelta(days=55),
    )

    # Initial total active units
    assert engine.get_total_active_count("A+") == 13

    # Run reclamation
    engine.scan_and_reclaim_expired_stock(reference_date=today)

    # BATCH-002 should now be disposed with 0 units
    item_exp = engine.get_stock_unit("BATCH-002")
    assert item_exp.status == "Disposed"
    assert item_exp.units == 0

    # BATCH-001 remains active with 8 units
    item_fresh = engine.get_stock_unit("BATCH-001")
    assert item_fresh.status == "Active"
    assert item_fresh.units == 8

    # Active count reduced to 8
    assert engine.get_total_active_count("A+") == 8


def test_disposal_audit_log_creation(engine, today):
    """Verifies disposal audit records are created with accurate metadata."""
    engine.add_stock_unit(
        sample_id="LOG-TEST-01",
        blood_group="B-",
        units=7,
        donated_date=today - timedelta(days=48),
        hospital_id="HOSP-CITY",
    )

    result = engine.scan_and_reclaim_expired_stock(reference_date=today)
    records = engine.get_disposal_records()

    assert len(records) == 1
    rec = records[0]
    assert rec.sample_id == "LOG-TEST-01"
    assert rec.blood_group == "B-"
    assert rec.units_disposed == 7
    assert rec.age_days == 48
    assert rec.hospital_id == "HOSP-CITY"
    assert "Exceeded 42-day storage threshold" in rec.reason
    assert rec.disposal_id.startswith("DISP-")
    assert rec.disposed_at is not None


def test_fresh_inventory_untouched(engine, today):
    """Verifies reclamation run leaves all fresh inventory completely intact."""
    engine.add_stock_unit(
        sample_id="FRESH-A",
        blood_group="A-",
        units=12,
        donated_date=today - timedelta(days=5),
    )
    engine.add_stock_unit(
        sample_id="FRESH-B",
        blood_group="O+",
        units=20,
        donated_date=today - timedelta(days=25),
    )

    result = engine.scan_and_reclaim_expired_stock(reference_date=today)

    assert result["expired_samples_count"] == 0
    assert result["total_units_reclaimed"] == 0
    assert engine.get_total_active_count() == 32
    assert len(engine.get_disposal_records()) == 0


def test_negative_units_validation():
    """Verifies negative units raise ValueError."""
    with pytest.raises(ValueError, match="cannot be negative"):
        BloodStockItem(
            sample_id="INVALID",
            blood_group="O+",
            units=-1,
            donated_date=date.today(),
        )
