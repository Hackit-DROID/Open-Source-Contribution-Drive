"""Unit tests for Multi-Unit Blood Inventory Splitting & Aliquot Unit Tracker (CR-802)."""

import os
import sys
from datetime import datetime, timedelta, timezone
import pytest

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from inventory.aliquot_tracker import (
    AliquotTrackerEngine,
    ChildAliquot,
    ParentBloodUnit,
)


@pytest.fixture
def tracker():
    """Returns a freshly initialized AliquotTrackerEngine instance."""
    return AliquotTrackerEngine()


@pytest.fixture
def sample_expiration():
    """Standard 42-day RBC expiration date."""
    return datetime.now(timezone.utc) + timedelta(days=42)


def test_register_parent_blood_unit(tracker, sample_expiration):
    """Parent unit registers correctly with given volume and donor metadata."""
    parent = tracker.register_parent_unit(
        unit_id="PAR-001",
        blood_group="O+",
        donor_id="DONOR-999",
        initial_volume_ml=450.0,
        expiration_date=sample_expiration,
    )

    assert parent.unit_id == "PAR-001"
    assert parent.blood_group == "O+"
    assert parent.donor_id == "DONOR-999"
    assert parent.initial_volume_ml == 450.0
    assert parent.available_volume_ml == 450.0
    assert parent.expiration_date == sample_expiration
    assert parent.status == "Active"


def test_split_creates_child_aliquots_linked_to_parent_id(tracker, sample_expiration):
    """Child aliquots reference parent_unit_id and preserve sequence indices."""
    tracker.register_parent_unit(
        unit_id="PAR-100",
        blood_group="A-",
        donor_id="DONOR-100",
        initial_volume_ml=450.0,
        expiration_date=sample_expiration,
    )

    res = tracker.split_parent_unit(
        parent_unit_id="PAR-100",
        aliquot_volumes=[100.0, 100.0, 100.0, 100.0],
    )

    assert len(res.aliquots_created) == 4
    for idx, aliquot in enumerate(res.aliquots_created, start=1):
        assert aliquot.parent_unit_id == "PAR-100"
        assert aliquot.aliquot_id == f"PAR-100-ALQ-{idx}"
        assert aliquot.aliquot_index == idx
        assert aliquot.volume_ml == 100.0


def test_child_aliquots_inherit_parent_metadata(tracker, sample_expiration):
    """Inherits parent blood group, donor ID, and expiration date across all child aliquots."""
    tracker.register_parent_unit(
        unit_id="PAR-200",
        blood_group="B+",
        donor_id="DONOR-200",
        initial_volume_ml=450.0,
        expiration_date=sample_expiration,
    )

    res = tracker.split_parent_unit(
        parent_unit_id="PAR-200",
        aliquot_volumes=[150.0, 150.0],
    )

    for aliquot in res.aliquots_created:
        assert aliquot.blood_group == "B+"
        assert aliquot.donor_id == "DONOR-200"
        assert aliquot.expiration_date == sample_expiration
        assert aliquot.status == "Active"


def test_reduces_parent_volume_and_adds_to_active_stock(tracker, sample_expiration):
    """Reduces available parent unit volume while adding child units to active stock."""
    parent = tracker.register_parent_unit(
        unit_id="PAR-300",
        blood_group="AB+",
        donor_id="DONOR-300",
        initial_volume_ml=450.0,
        expiration_date=sample_expiration,
    )

    # Initial stock has 0 child aliquots
    assert len(tracker.get_active_stock()) == 0

    res = tracker.split_parent_unit(
        parent_unit_id="PAR-300",
        aliquot_volumes=[100.0, 100.0],
    )

    assert res.remaining_parent_volume_ml == 250.0
    assert parent.available_volume_ml == 250.0
    assert parent.status == "Active"

    # Child units are now in active stock
    active_stock = tracker.get_active_stock()
    assert len(active_stock) == 2
    assert tracker.get_child_aliquot("PAR-300-ALQ-1") is not None
    assert tracker.get_child_aliquot("PAR-300-ALQ-2") is not None


def test_verify_volume_balance_calculations(tracker, sample_expiration):
    """Parent initial volume equals available volume plus total child aliquot volumes."""
    tracker.register_parent_unit(
        unit_id="PAR-400",
        blood_group="O-",
        donor_id="DONOR-400",
        initial_volume_ml=450.0,
        expiration_date=sample_expiration,
    )

    tracker.split_parent_unit(
        parent_unit_id="PAR-400",
        aliquot_volumes=[120.0, 80.0],
    )

    balance = tracker.verify_volume_balance("PAR-400")
    assert balance["is_balanced"] is True
    assert balance["initial_volume_ml"] == 450.0
    assert balance["available_volume_ml"] == 250.0
    assert balance["aliquoted_volume_ml"] == 200.0
    assert balance["child_units_count"] == 2
    assert balance["volume_difference_ml"] == 0.0


def test_full_depletion_when_all_volume_aliquoted(tracker, sample_expiration):
    """Status updates to 'Depleted' when parent volume reaches 0ml."""
    parent = tracker.register_parent_unit(
        unit_id="PAR-500",
        blood_group="A+",
        donor_id="DONOR-500",
        initial_volume_ml=450.0,
        expiration_date=sample_expiration,
    )

    res = tracker.split_parent_unit(
        parent_unit_id="PAR-500",
        aliquot_volumes=[100.0, 100.0, 100.0, 100.0, 50.0],
    )

    assert res.remaining_parent_volume_ml == 0.0
    assert parent.available_volume_ml == 0.0
    assert parent.status == "Depleted"

    balance = tracker.verify_volume_balance("PAR-500")
    assert balance["is_balanced"] is True
    assert balance["aliquoted_volume_ml"] == 450.0

    # Cannot split a depleted parent unit
    with pytest.raises(ValueError, match="is Depleted"):
        tracker.split_parent_unit("PAR-500", [10.0])


def test_split_exceeding_available_volume_fails(tracker, sample_expiration):
    """Attempting to request more volume than available raises ValueError."""
    tracker.register_parent_unit(
        unit_id="PAR-600",
        blood_group="O+",
        donor_id="DONOR-600",
        initial_volume_ml=450.0,
        expiration_date=sample_expiration,
    )

    with pytest.raises(ValueError, match="exceeds available parent unit volume"):
        tracker.split_parent_unit("PAR-600", [300.0, 200.0])


def test_lineage_verification(tracker, sample_expiration):
    """Lineage audit confirms consistency between child and parent units."""
    tracker.register_parent_unit(
        unit_id="PAR-700",
        blood_group="B-",
        donor_id="DONOR-700",
        initial_volume_ml=450.0,
        expiration_date=sample_expiration,
    )

    tracker.split_parent_unit(
        parent_unit_id="PAR-700",
        aliquot_volumes=[100.0],
    )

    lineage = tracker.verify_lineage("PAR-700-ALQ-1")
    assert lineage["is_valid"] is True
    assert lineage["blood_group_matches"] is True
    assert lineage["donor_matches"] is True
    assert lineage["expiration_matches"] is True
    assert lineage["parent_details"]["unit_id"] == "PAR-700"
    assert lineage["aliquot_details"]["volume_ml"] == 100.0


def test_sequential_multi_stage_splitting(tracker, sample_expiration):
    """Multiple sequential split operations correctly maintain indices and volume."""
    parent = tracker.register_parent_unit(
        unit_id="PAR-800",
        blood_group="O+",
        donor_id="DONOR-800",
        initial_volume_ml=450.0,
        expiration_date=sample_expiration,
    )

    res1 = tracker.split_parent_unit("PAR-800", [100.0, 100.0])
    assert res1.remaining_parent_volume_ml == 250.0
    assert len(tracker.get_child_aliquots("PAR-800")) == 2

    res2 = tracker.split_parent_unit("PAR-800", [50.0, 50.0])
    assert res2.remaining_parent_volume_ml == 150.0
    assert len(tracker.get_child_aliquots("PAR-800")) == 4

    assert res2.aliquots_created[0].aliquot_id == "PAR-800-ALQ-3"
    assert res2.aliquots_created[1].aliquot_id == "PAR-800-ALQ-4"

    balance = tracker.verify_volume_balance("PAR-800")
    assert balance["is_balanced"] is True
    assert balance["available_volume_ml"] == 150.0
    assert balance["aliquoted_volume_ml"] == 300.0


def test_active_stock_filtering_by_blood_group(tracker, sample_expiration):
    """Filter active stock by blood group."""
    tracker.register_parent_unit("PAR-A", "A+", "D-A", 450.0, sample_expiration)
    tracker.register_parent_unit("PAR-B", "B+", "D-B", 450.0, sample_expiration)

    tracker.split_parent_unit("PAR-A", [100.0, 100.0])
    tracker.split_parent_unit("PAR-B", [100.0])

    assert len(tracker.get_active_stock()) == 3
    assert len(tracker.get_active_stock("A+")) == 2
    assert len(tracker.get_active_stock("B+")) == 1
    assert len(tracker.get_active_stock("O+")) == 0
