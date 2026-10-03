"""Multi-Hospital Blood Stock Sharing Agreement & Ratio Ledger (CR-701).

Tracks inter-hospital blood unit exchanges, calculates net transfer balances
(Units Sent - Units Received), enforces sharing agreements, and flags quota
imbalances across participating regional hospital networks.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


DEFAULT_QUOTA_THRESHOLD = 50


@dataclass
class HospitalTransfer:
    """Represents a recorded transfer of blood units between two hospitals."""
    transfer_id: str
    from_hospital_id: str
    from_hospital_name: str
    to_hospital_id: str
    to_hospital_name: str
    blood_group: str
    units: int
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    notes: str = ""

    def __post_init__(self):
        self.blood_group = self.blood_group.strip().upper()
        if self.units <= 0:
            raise ValueError(f"Transfer units must be positive, got {self.units}")
        if self.from_hospital_id == self.to_hospital_id:
            raise ValueError("Source and destination hospital cannot be the same.")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "transfer_id": self.transfer_id,
            "from_hospital_id": self.from_hospital_id,
            "from_hospital_name": self.from_hospital_name,
            "to_hospital_id": self.to_hospital_id,
            "to_hospital_name": self.to_hospital_name,
            "blood_group": self.blood_group,
            "units": self.units,
            "timestamp": self.timestamp.isoformat(),
            "notes": self.notes,
        }


@dataclass
class HospitalBalanceRecord:
    """Maintains exchange balance and quota standing for a participating hospital."""
    hospital_id: str
    hospital_name: str
    units_sent: int = 0
    units_received: int = 0
    quota_threshold: int = DEFAULT_QUOTA_THRESHOLD

    @property
    def net_balance(self) -> int:
        """Net transfer balance = Units Sent - Units Received."""
        return self.units_sent - self.units_received

    @property
    def is_imbalanced(self) -> bool:
        """Flags quota imbalance when absolute net transfer exceeds quota threshold."""
        return abs(self.net_balance) > self.quota_threshold

    @property
    def imbalance_type(self) -> str:
        """Categorizes quota standing: SURPLUS_DONOR, DEFICIT_RECEIVER, or BALANCED."""
        if self.net_balance > self.quota_threshold:
            return "SURPLUS_DONOR"
        elif self.net_balance < -self.quota_threshold:
            return "DEFICIT_RECEIVER"
        return "BALANCED"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hospital_id": self.hospital_id,
            "hospital_name": self.hospital_name,
            "units_sent": self.units_sent,
            "units_received": self.units_received,
            "net_balance": self.net_balance,
            "quota_threshold": self.quota_threshold,
            "is_imbalanced": self.is_imbalanced,
            "imbalance_type": self.imbalance_type,
        }


class BloodStockSharingLedger:
    """Ledger tracking blood unit exchanges and quota ratios between hospitals."""

    def __init__(self, default_quota_threshold: int = DEFAULT_QUOTA_THRESHOLD):
        if default_quota_threshold < 0:
            raise ValueError("Quota threshold cannot be negative.")
        self.default_quota_threshold = default_quota_threshold
        self._hospitals: Dict[str, HospitalBalanceRecord] = {}
        self._transfers: List[HospitalTransfer] = []

    def register_hospital(
        self,
        hospital_id: str,
        hospital_name: str,
        quota_threshold: Optional[int] = None,
    ) -> HospitalBalanceRecord:
        """Register a participating hospital in the sharing network."""
        threshold = (
            quota_threshold if quota_threshold is not None else self.default_quota_threshold
        )
        if threshold < 0:
            raise ValueError("Quota threshold cannot be negative.")
        record = HospitalBalanceRecord(
            hospital_id=hospital_id,
            hospital_name=hospital_name,
            quota_threshold=threshold,
        )
        self._hospitals[hospital_id] = record
        return record

    def get_hospital(self, hospital_id: str) -> Optional[HospitalBalanceRecord]:
        """Retrieve balance record for a hospital by ID."""
        return self._hospitals.get(hospital_id)

    @staticmethod
    def calculate_net_balance(units_sent: int, units_received: int) -> int:
        """Calculate net balance formula: units_sent - units_received."""
        if units_sent < 0 or units_received < 0:
            raise ValueError("Units sent and received must be non-negative.")
        return units_sent - units_received

    @staticmethod
    def check_quota_imbalance(net_balance: int, quota_threshold: int) -> bool:
        """Determine if net transfer exceeds quota threshold."""
        return abs(net_balance) > quota_threshold

    def record_transfer(
        self,
        transfer_id: str,
        from_hospital_id: str,
        to_hospital_id: str,
        blood_group: str,
        units: int,
        from_hospital_name: Optional[str] = None,
        to_hospital_name: Optional[str] = None,
        notes: str = "",
    ) -> HospitalTransfer:
        """Record a blood stock transfer between two hospitals and update balances."""
        if units <= 0:
            raise ValueError(f"Transfer units must be positive, got {units}")
        if from_hospital_id == to_hospital_id:
            raise ValueError("Source and destination hospital cannot be identical.")

        # Auto-register hospitals if not already present
        if from_hospital_id not in self._hospitals:
            name = from_hospital_name or f"Hospital-{from_hospital_id}"
            self.register_hospital(from_hospital_id, name)
        if to_hospital_id not in self._hospitals:
            name = to_hospital_name or f"Hospital-{to_hospital_id}"
            self.register_hospital(to_hospital_id, name)

        sender = self._hospitals[from_hospital_id]
        receiver = self._hospitals[to_hospital_id]

        transfer = HospitalTransfer(
            transfer_id=transfer_id,
            from_hospital_id=from_hospital_id,
            from_hospital_name=sender.hospital_name,
            to_hospital_id=to_hospital_id,
            to_hospital_name=receiver.hospital_name,
            blood_group=blood_group,
            units=units,
            notes=notes,
        )

        sender.units_sent += units
        receiver.units_received += units
        self._transfers.append(transfer)
        return transfer

    def get_all_balances(self) -> List[HospitalBalanceRecord]:
        """Return list of balance records for all registered hospitals."""
        return list(self._hospitals.values())

    def get_imbalanced_hospitals(self) -> List[HospitalBalanceRecord]:
        """Return list of hospitals exceeding their quota threshold."""
        return [h for h in self._hospitals.values() if h.is_imbalanced]

    def get_transfers_for_hospital(self, hospital_id: str) -> List[HospitalTransfer]:
        """Return all transfers involving a given hospital (as sender or receiver)."""
        return [
            t for t in self._transfers
            if t.from_hospital_id == hospital_id or t.to_hospital_id == hospital_id
        ]

    def get_network_summary(self) -> Dict[str, Any]:
        """Generate network-wide sharing ledger summary metrics."""
        total_transfers = len(self._transfers)
        total_units_transferred = sum(t.units for t in self._transfers)
        imbalanced = self.get_imbalanced_hospitals()
        return {
            "total_participating_hospitals": len(self._hospitals),
            "total_transfers_recorded": total_transfers,
            "total_units_transferred": total_units_transferred,
            "imbalanced_hospitals_count": len(imbalanced),
            "imbalanced_hospitals": [h.to_dict() for h in imbalanced],
            "balances": [h.to_dict() for h in self._hospitals.values()],
        }
