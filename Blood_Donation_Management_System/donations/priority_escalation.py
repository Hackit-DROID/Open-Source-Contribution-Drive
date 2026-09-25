"""Emergency Blood Request Priority Escalation Workflow.

Implements priority-based blood request queue management, urgency level classification
('Routine', 'Urgent', 'Emergency ICU'), automated promotion of critical ICU requests,
and compatible unit identification for emergency medical cases.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from donations.compatibility import get_compatible_donor_types, is_compatible


class UrgencyLevel(str, Enum):
    """Urgency classification levels for blood donation requests."""
    ROUTINE = "Routine"
    URGENT = "Urgent"
    EMERGENCY_ICU = "Emergency ICU"


# Numeric weights for queue sorting: higher weight = higher dispatch priority
URGENCY_WEIGHTS: Dict[str, int] = {
    UrgencyLevel.EMERGENCY_ICU.value: 100,
    UrgencyLevel.URGENT.value: 50,
    UrgencyLevel.ROUTINE.value: 10,
}


def normalize_urgency_level(level: str) -> str:
    """Normalize input string to standard UrgencyLevel representation."""
    if not level or not isinstance(level, str):
        return UrgencyLevel.ROUTINE.value
    cleaned = level.strip().lower()
    if cleaned in ("emergency icu", "emergency_icu", "emergency", "icu"):
        return UrgencyLevel.EMERGENCY_ICU.value
    if cleaned in ("urgent", "high", "priority"):
        return UrgencyLevel.URGENT.value
    if cleaned in ("routine", "standard", "normal", "low"):
        return UrgencyLevel.ROUTINE.value
    return UrgencyLevel.ROUTINE.value


def get_urgency_weight(level: str) -> int:
    """Return priority weight corresponding to an urgency level."""
    normalized = normalize_urgency_level(level)
    return URGENCY_WEIGHTS.get(normalized, 10)


@dataclass
class BloodRequestItem:
    """Represents a hospital blood request with urgency metadata."""
    request_id: str
    patient_name: str
    blood_group: str
    units: int
    hospital: str
    urgency_level: str = UrgencyLevel.ROUTINE.value
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "Pending"
    escalation_reason: Optional[str] = None

    def __post_init__(self):
        self.urgency_level = normalize_urgency_level(self.urgency_level)
        self.blood_group = self.blood_group.strip().upper() if self.blood_group else "O+"

    @property
    def urgency_weight(self) -> int:
        return get_urgency_weight(self.urgency_level)

    @property
    def is_emergency(self) -> bool:
        return self.urgency_level == UrgencyLevel.EMERGENCY_ICU.value

    def escalate(self, new_level: str, reason: str = "") -> None:
        """Escalate the request urgency level with audit reason."""
        self.urgency_level = normalize_urgency_level(new_level)
        self.escalation_reason = reason or f"Escalated to {self.urgency_level}"


class EmergencyPriorityQueue:
    """Manages blood requests in an urgency-ranked, FIFO-ordered queue."""

    def __init__(self):
        self._requests: Dict[str, BloodRequestItem] = {}
        self._audit_log: List[Dict[str, Any]] = []

    def add_request(self, request: BloodRequestItem) -> None:
        """Insert or update a blood request in the queue."""
        self._requests[request.request_id] = request
        self._log_event("REQUEST_ADDED", request.request_id, {
            "urgency": request.urgency_level,
            "blood_group": request.blood_group,
            "units": request.units,
            "hospital": request.hospital,
        })

    def get_request(self, request_id: str) -> Optional[BloodRequestItem]:
        """Fetch request item by its identifier."""
        return self._requests.get(request_id)

    def promote_to_emergency(self, request_id: str, reason: str = "Critical patient status") -> BloodRequestItem:
        """Promote an existing request directly to Emergency ICU status."""
        item = self._requests.get(request_id)
        if not item:
            raise KeyError(f"Request ID '{request_id}' not found in queue.")
        previous_level = item.urgency_level
        item.escalate(UrgencyLevel.EMERGENCY_ICU.value, reason=reason)
        self._log_event("PRIORITY_ESCALATED", request_id, {
            "from": previous_level,
            "to": item.urgency_level,
            "reason": reason,
        })
        return item

    def get_prioritized_queue(self, status: Optional[str] = "Pending") -> List[BloodRequestItem]:
        """Return requests ordered by priority:
        1. Urgency weight descending ('Emergency ICU' > 'Urgent' > 'Routine')
        2. Creation timestamp ascending (FIFO order within same urgency)
        """
        items = list(self._requests.values())
        if status:
            items = [item for item in items if item.status.lower() == status.lower()]

        # Sort: higher weight (-weight) first, then earlier created_at first
        items.sort(key=lambda r: (-r.urgency_weight, r.created_at))
        return items

    def match_compatible_inventory(
        self,
        request_id: str,
        available_inventory: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify immediate compatible blood units from available inventory for a request."""
        req = self._requests.get(request_id)
        if not req:
            raise KeyError(f"Request ID '{request_id}' not found.")

        compatible_types = get_compatible_donor_types(req.blood_group)
        matched_units = [
            unit for unit in available_inventory
            if unit.get("blood_group", "").strip().upper() in compatible_types
            and unit.get("status", "Available").lower() == "available"
        ]
        return matched_units

    def _log_event(self, event_type: str, request_id: str, details: Dict[str, Any]) -> None:
        self._audit_log.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "request_id": request_id,
            "details": details,
        })

    @property
    def audit_log(self) -> List[Dict[str, Any]]:
        return list(self._audit_log)
