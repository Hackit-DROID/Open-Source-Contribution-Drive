"""Automated Emergency Blood Shortage Notification & Broadcast Dispatcher (CR-801).

Detects critical inventory shortages (< 2 units), filters eligible matching donors
based on minimum donation intervals (> 56 days elapsed), formats outreach broadcast
payloads, and maintains audit dispatch logs.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
import uuid

from donations.compatibility import get_compatible_donor_types


@dataclass
class DonorProfile:
    """Donor profile including historical donation date and contact details."""
    donor_id: str
    name: str
    blood_group: str
    contact: str = ""
    city: str = ""
    last_donated_at: Optional[datetime] = None

    def __post_init__(self):
        self.blood_group = self.blood_group.strip().upper()

    def is_eligible(
        self,
        current_date: Optional[datetime] = None,
        min_interval_days: int = 56
    ) -> bool:
        """Verify whether donor is eligible to donate based on 56-day cooldown.

        Donors with no prior donation history are immediately eligible.
        """
        if self.last_donated_at is None:
            return True
        now = current_date or datetime.now(timezone.utc)
        # Normalize timezone awareness
        if self.last_donated_at.tzinfo is None and now.tzinfo is not None:
            last = self.last_donated_at.replace(tzinfo=timezone.utc)
        elif self.last_donated_at.tzinfo is not None and now.tzinfo is None:
            last = self.last_donated_at.astimezone(timezone.utc).replace(tzinfo=None)
        else:
            last = self.last_donated_at

        elapsed = now - last
        return elapsed >= timedelta(days=min_interval_days)


@dataclass
class BroadcastDispatchPayload:
    """Payload representing an emergency broadcast dispatch to eligible donors."""
    broadcast_id: str
    blood_group: str
    current_units: int
    recipient_count: int
    target_donors: List[Dict[str, Any]]
    message: str
    dispatched_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "Dispatched"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "broadcast_id": self.broadcast_id,
            "blood_group": self.blood_group,
            "current_units": self.current_units,
            "recipient_count": self.recipient_count,
            "target_donors": self.target_donors,
            "message": self.message,
            "dispatched_at": self.dispatched_at.isoformat(),
            "status": self.status,
        }


class EmergencyBroadcastDispatcher:
    """Manages shortage detection, eligible donor filtering, and emergency broadcast dispatching."""

    def __init__(self, critical_threshold: int = 2):
        self.critical_threshold = critical_threshold
        self._inventory: Dict[str, int] = {}
        self._donors: Dict[str, DonorProfile] = {}
        self._dispatch_log: List[BroadcastDispatchPayload] = []

    def set_stock(self, blood_group: str, units: int) -> None:
        """Update active unit stock for a blood group."""
        self._inventory[blood_group.strip().upper()] = max(0, units)

    def get_stock(self, blood_group: str) -> int:
        """Get current inventory units for a blood group."""
        return self._inventory.get(blood_group.strip().upper(), 0)

    def register_donor(self, donor: DonorProfile) -> None:
        """Register or update a donor in the contact pool."""
        self._donors[donor.donor_id] = donor

    def detect_critical_shortages(self) -> List[str]:
        """Detect all blood groups where available stock is below the critical threshold (< 2 units)."""
        shortages = []
        for bg, units in self._inventory.items():
            if units < self.critical_threshold:
                shortages.append(bg)
        shortages.sort()
        return shortages

    def is_critical_shortage(self, blood_group: str) -> bool:
        """Check if a specific blood group has < 2 units in stock."""
        return self.get_stock(blood_group) < self.critical_threshold

    def filter_eligible_donors(
        self,
        blood_group: str,
        as_of_date: Optional[datetime] = None,
        include_compatible: bool = False
    ) -> List[DonorProfile]:
        """Filter donors matching the target blood group who have not donated in the past 56 days."""
        target_bg = blood_group.strip().upper()
        if include_compatible:
            valid_groups = set(get_compatible_donor_types(target_bg))
        else:
            valid_groups = {target_bg}

        eligible: List[DonorProfile] = []
        for donor in self._donors.values():
            if donor.blood_group in valid_groups and donor.is_eligible(current_date=as_of_date):
                eligible.append(donor)

        # Sort alphabetically by donor name
        eligible.sort(key=lambda d: d.name)
        return eligible

    def dispatch_emergency_broadcast(
        self,
        blood_group: str,
        as_of_date: Optional[datetime] = None,
        custom_message: Optional[str] = None
    ) -> BroadcastDispatchPayload:
        """Trigger an emergency outreach broadcast for a shortage blood group."""
        bg = blood_group.strip().upper()
        current_units = self.get_stock(bg)

        # Find eligible donors
        eligible_donors = self.filter_eligible_donors(bg, as_of_date=as_of_date)

        target_summary = [
            {
                "donor_id": d.donor_id,
                "name": d.name,
                "blood_group": d.blood_group,
                "contact": d.contact,
                "city": d.city,
                "last_donated_at": d.last_donated_at.isoformat() if d.last_donated_at else None,
            }
            for d in eligible_donors
        ]

        default_msg = (
            f"URGENT: Critical shortage of {bg} blood ({current_units} units remaining). "
            f"Eligible donors are urgently requested to visit their nearest donation center."
        )

        payload = BroadcastDispatchPayload(
            broadcast_id=f"BC-{uuid.uuid4().hex[:8].upper()}",
            blood_group=bg,
            current_units=current_units,
            recipient_count=len(target_summary),
            target_donors=target_summary,
            message=custom_message or default_msg,
            dispatched_at=as_of_date or datetime.now(timezone.utc),
            status="Dispatched",
        )

        self._dispatch_log.append(payload)
        return payload

    @property
    def dispatch_audit_log(self) -> List[BroadcastDispatchPayload]:
        """Return historical record of all dispatched emergency notifications."""
        return list(self._dispatch_log)
