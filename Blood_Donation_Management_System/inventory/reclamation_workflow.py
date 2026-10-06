"""Blood Inventory Expiry Audit & Automated Stock Reclamation Workflow (CR-616).

Enables blood banks to automatically scan inventory units against the 42-day storage
threshold (standard shelf life for whole blood/RBCs), identify expired units,
deduct expired units from active stock counts, transition status to 'Disposed',
and record auditable disposal logs.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
import uuid


DEFAULT_STORAGE_THRESHOLD_DAYS: int = 42


@dataclass
class BloodStockItem:
    """Represents an individual blood stock batch/unit in inventory."""
    sample_id: str
    blood_group: str
    units: int
    donated_date: date
    hospital_id: Optional[str] = None
    status: str = "Active"  # "Active", "Expired", "Disposed"

    def __post_init__(self):
        self.sample_id = str(self.sample_id).strip()
        self.blood_group = str(self.blood_group).strip().upper()
        if self.units < 0:
            raise ValueError(f"Units cannot be negative, got {self.units}")
        if isinstance(self.donated_date, datetime):
            self.donated_date = self.donated_date.date()

    def get_age_days(self, reference_date: Optional[date] = None) -> int:
        """Calculates age in days relative to reference date (default today)."""
        ref = reference_date or date.today()
        return (ref - self.donated_date).days

    def is_expired(
        self,
        threshold_days: int = DEFAULT_STORAGE_THRESHOLD_DAYS,
        reference_date: Optional[date] = None,
    ) -> bool:
        """Returns True if the blood unit has exceeded the storage threshold."""
        return self.get_age_days(reference_date=reference_date) > threshold_days

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sample_id": self.sample_id,
            "blood_group": self.blood_group,
            "units": self.units,
            "donated_date": self.donated_date.isoformat(),
            "hospital_id": self.hospital_id,
            "status": self.status,
            "age_days": self.get_age_days(),
        }


@dataclass
class DisposalAuditRecord:
    """Audit record capturing the reclamation and disposal of expired blood units."""
    disposal_id: str
    sample_id: str
    blood_group: str
    units_disposed: int
    age_days: int
    disposed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    reason: str = "Exceeded 42-day storage threshold"
    hospital_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "disposal_id": self.disposal_id,
            "sample_id": self.sample_id,
            "blood_group": self.blood_group,
            "units_disposed": self.units_disposed,
            "age_days": self.age_days,
            "disposed_at": self.disposed_at.isoformat(),
            "reason": self.reason,
            "hospital_id": self.hospital_id,
        }


class BloodInventoryReclamationEngine:
    """
    Automated inventory reclamation engine scanning blood stock units,
    calculating storage shelf life, updating expired unit status, deducting
    units from active counts, and logging disposal events.
    """

    def __init__(self, storage_threshold_days: int = DEFAULT_STORAGE_THRESHOLD_DAYS):
        self.storage_threshold_days = storage_threshold_days
        self._inventory: Dict[str, BloodStockItem] = {}
        self._disposal_audit_log: List[DisposalAuditRecord] = []

    def add_stock_unit(
        self,
        sample_id: str,
        blood_group: str,
        units: int,
        donated_date: date,
        hospital_id: Optional[str] = None,
        status: str = "Active",
    ) -> BloodStockItem:
        """Registers a blood stock unit into the tracking engine."""
        item = BloodStockItem(
            sample_id=sample_id,
            blood_group=blood_group,
            units=units,
            donated_date=donated_date,
            hospital_id=hospital_id,
            status=status,
        )
        self._inventory[item.sample_id] = item
        return item

    def get_stock_unit(self, sample_id: str) -> Optional[BloodStockItem]:
        return self._inventory.get(sample_id)

    def get_active_units(self, blood_group: Optional[str] = None) -> List[BloodStockItem]:
        """Returns list of active blood stock units."""
        items = [
            item for item in self._inventory.values()
            if item.status == "Active" and item.units > 0
        ]
        if blood_group:
            bg = blood_group.strip().upper()
            items = [item for item in items if item.blood_group == bg]
        return items

    def get_total_active_count(self, blood_group: Optional[str] = None) -> int:
        """Computes total available units in active stock."""
        return sum(item.units for item in self.get_active_units(blood_group=blood_group))

    def get_disposal_records(self) -> List[DisposalAuditRecord]:
        return list(self._disposal_audit_log)

    def scan_and_reclaim_expired_stock(
        self,
        reference_date: Optional[date] = None,
        reason: str = "Exceeded 42-day storage threshold",
    ) -> Dict[str, Any]:
        """
        Executes the automated inventory reclamation workflow:
        1. Identifies blood stock units exceeding 42-day storage threshold.
        2. Deducts expired units from active stock counts and marks status as 'Disposed'.
        3. Generates disposal audit records for each expired unit.
        """
        ref_date = reference_date or date.today()
        scanned_count = 0
        expired_units_reclaimed = 0
        disposed_samples: List[DisposalAuditRecord] = []

        for sample_id, item in list(self._inventory.items()):
            if item.status != "Active":
                continue

            scanned_count += 1
            age_days = item.get_age_days(reference_date=ref_date)

            if age_days > self.storage_threshold_days:
                units_to_dispose = item.units
                # Deduct units from active stock
                item.units = 0
                item.status = "Disposed"
                expired_units_reclaimed += units_to_dispose

                # Create audit log record
                record = DisposalAuditRecord(
                    disposal_id=f"DISP-{uuid.uuid4().hex[:8].upper()}",
                    sample_id=item.sample_id,
                    blood_group=item.blood_group,
                    units_disposed=units_to_dispose,
                    age_days=age_days,
                    disposed_at=datetime.now(timezone.utc),
                    reason=reason,
                    hospital_id=item.hospital_id,
                )
                self._disposal_audit_log.append(record)
                disposed_samples.append(record)

        return {
            "scanned_samples": scanned_count,
            "expired_samples_count": len(disposed_samples),
            "total_units_reclaimed": expired_units_reclaimed,
            "disposal_records": [r.to_dict() for r in disposed_samples],
            "active_units_remaining": self.get_total_active_count(),
            "status": "COMPLETED",
        }
