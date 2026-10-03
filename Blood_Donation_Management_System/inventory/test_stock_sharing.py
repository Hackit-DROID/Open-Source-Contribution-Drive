"""Unit tests for Multi-Hospital Blood Stock Sharing Agreement & Ratio Ledger (CR-701)."""

import os
import sys
from datetime import datetime, timezone
import pytest

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from inventory.stock_sharing import (
    BloodStockSharingLedger,
    HospitalTransfer,
    HospitalBalanceRecord,
    DEFAULT_QUOTA_THRESHOLD,
)


@pytest.fixture
def ledger():
    """Returns a freshly initialized BloodStockSharingLedger."""
    return BloodStockSharingLedger(default_quota_threshold=50)


def test_calculate_net_balance_formula():
    """Verifies net balance calculation: Units Sent - Units Received."""
    # Positive net balance (sent > received)
    assert BloodStockSharingLedger.calculate_net_balance(units_sent=100, units_received=30) == 70
    # Negative net balance (received > sent)
    assert BloodStockSharingLedger.calculate_net_balance(units_sent=20, units_received=50) == -30
    # Zero net balance
    assert BloodStockSharingLedger.calculate_net_balance(units_sent=40, units_received=40) == 0


def test_calculate_net_balance_validation():
    """Rejects negative values for units sent or received."""
    with pytest.raises(ValueError, match="non-negative"):
        BloodStockSharingLedger.calculate_net_balance(units_sent=-5, units_received=10)
    with pytest.raises(ValueError, match="non-negative"):
        BloodStockSharingLedger.calculate_net_balance(units_sent=10, units_received=-5)


def test_hospital_registration_and_retrieval(ledger):
    """Registers hospitals and retrieves balance records."""
    h1 = ledger.register_hospital("HOSP-1", "Memorial Hospital", quota_threshold=60)
    assert h1.hospital_id == "HOSP-1"
    assert h1.hospital_name == "Memorial Hospital"
    assert h1.units_sent == 0
    assert h1.units_received == 0
    assert h1.net_balance == 0
    assert h1.quota_threshold == 60
    assert h1.is_imbalanced is False
    assert h1.imbalance_type == "BALANCED"

    retrieved = ledger.get_hospital("HOSP-1")
    assert retrieved is not None
    assert retrieved.hospital_id == "HOSP-1"


def test_record_transfer_updates_balances(ledger):
    """Records a transfer between hospitals and accurately updates both balances."""
    ledger.register_hospital("HOSP-A", "City General", quota_threshold=50)
    ledger.register_hospital("HOSP-B", "St. Jude Hospital", quota_threshold=50)

    transfer = ledger.record_transfer(
        transfer_id="TR-001",
        from_hospital_id="HOSP-A",
        to_hospital_id="HOSP-B",
        blood_group="O+",
        units=25,
        notes="Emergency supply transfer",
    )

    assert transfer.transfer_id == "TR-001"
    assert transfer.units == 25
    assert transfer.blood_group == "O+"

    hosp_a = ledger.get_hospital("HOSP-A")
    hosp_b = ledger.get_hospital("HOSP-B")

    # HOSP-A sent 25 units -> net balance = +25
    assert hosp_a.units_sent == 25
    assert hosp_a.units_received == 0
    assert hosp_a.net_balance == 25
    assert hosp_a.is_imbalanced is False

    # HOSP-B received 25 units -> net balance = -25
    assert hosp_b.units_sent == 0
    assert hosp_b.units_received == 25
    assert hosp_b.net_balance == -25
    assert hosp_b.is_imbalanced is False


def test_quota_imbalance_detection_surplus_and_deficit(ledger):
    """Flags quota imbalance when net transfer exceeds quota threshold."""
    ledger.register_hospital("HOSP-DONOR", "Regional Blood Center", quota_threshold=50)
    ledger.register_hospital("HOSP-CLINIC", "Metro Clinic", quota_threshold=50)

    # First transfer within quota (40 units)
    ledger.record_transfer("TR-101", "HOSP-DONOR", "HOSP-CLINIC", "A-", 40)
    donor = ledger.get_hospital("HOSP-DONOR")
    clinic = ledger.get_hospital("HOSP-CLINIC")
    assert donor.is_imbalanced is False
    assert clinic.is_imbalanced is False
    assert donor.imbalance_type == "BALANCED"

    # Second transfer pushes net balance over threshold (+65 > 50, -65 < -50)
    ledger.record_transfer("TR-102", "HOSP-DONOR", "HOSP-CLINIC", "A-", 25)
    assert donor.net_balance == 65
    assert donor.is_imbalanced is True
    assert donor.imbalance_type == "SURPLUS_DONOR"

    assert clinic.net_balance == -65
    assert clinic.is_imbalanced is True
    assert clinic.imbalance_type == "DEFICIT_RECEIVER"

    imbalanced = ledger.get_imbalanced_hospitals()
    imbalanced_ids = {h.hospital_id for h in imbalanced}
    assert imbalanced_ids == {"HOSP-DONOR", "HOSP-CLINIC"}


def test_exact_threshold_boundary():
    """Verifies that balance exactly at threshold is not marked imbalanced (strict >)."""
    assert BloodStockSharingLedger.check_quota_imbalance(net_balance=50, quota_threshold=50) is False
    assert BloodStockSharingLedger.check_quota_imbalance(net_balance=-50, quota_threshold=50) is False
    assert BloodStockSharingLedger.check_quota_imbalance(net_balance=51, quota_threshold=50) is True
    assert BloodStockSharingLedger.check_quota_imbalance(net_balance=-51, quota_threshold=50) is True


def test_invalid_transfer_validation(ledger):
    """Rejects invalid transfers such as zero units, negative units, or self-transfers."""
    ledger.register_hospital("HOSP-1", "Hospital 1")
    ledger.register_hospital("HOSP-2", "Hospital 2")

    with pytest.raises(ValueError, match="positive"):
        ledger.record_transfer("TR-X1", "HOSP-1", "HOSP-2", "O+", 0)

    with pytest.raises(ValueError, match="positive"):
        ledger.record_transfer("TR-X2", "HOSP-1", "HOSP-2", "O+", -10)

    with pytest.raises(ValueError, match="identical|same"):
        ledger.record_transfer("TR-X3", "HOSP-1", "HOSP-1", "O+", 15)


def test_multi_hospital_network_rebalancing(ledger):
    """Verifies multi-party exchanges and returning to balanced state."""
    ledger.register_hospital("H1", "Hospital 1", quota_threshold=30)
    ledger.register_hospital("H2", "Hospital 2", quota_threshold=30)
    ledger.register_hospital("H3", "Hospital 3", quota_threshold=30)

    # H1 sends 40 to H2 (H1 is +40 imbalanced, H2 is -40 imbalanced)
    ledger.record_transfer("T1", "H1", "H2", "B+", 40)
    assert ledger.get_hospital("H1").is_imbalanced is True
    assert ledger.get_hospital("H2").is_imbalanced is True

    # H2 sends 25 to H3 (H2 net becomes -40 + 25 = -15, which is balanced!)
    ledger.record_transfer("T2", "H2", "H3", "B+", 25)
    assert ledger.get_hospital("H2").net_balance == -15
    assert ledger.get_hospital("H2").is_imbalanced is False

    # H3 sends 20 to H1 (H1 net becomes +40 - 20 = +20, balanced!)
    ledger.record_transfer("T3", "H3", "H1", "B+", 20)
    assert ledger.get_hospital("H1").net_balance == 20
    assert ledger.get_hospital("H1").is_imbalanced is False


def test_network_summary_and_transfers_lookup(ledger):
    """Verifies network summary metrics and hospital transfer queries."""
    ledger.record_transfer("TR-A", "HA", "HB", "AB+", 10, "Hospital A", "Hospital B")
    ledger.record_transfer("TR-B", "HB", "HC", "AB-", 15, "Hospital B", "Hospital C")

    summary = ledger.get_network_summary()
    assert summary["total_participating_hospitals"] == 3
    assert summary["total_transfers_recorded"] == 2
    assert summary["total_units_transferred"] == 25

    hb_transfers = ledger.get_transfers_for_hospital("HB")
    assert len(hb_transfers) == 2
