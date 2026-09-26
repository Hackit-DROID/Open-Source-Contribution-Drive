"""Multi-Unit Blood Inventory Splitting & Aliquot Unit Tracker (CR-802).

Enables blood banks to split parent blood bags into child pediatric aliquot units
while preserving parent-child unit lineage, inheriting vital donor metadata
(blood group, donor ID, expiration date), reducing parent available volume,
and tracking active stock balance.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid


@dataclass
class ChildAliquot:
    """Represents a child pediatric aliquot derived from a parent blood unit."""
    aliquot_id: str
    parent_unit_id: str
    aliquot_index: int
    volume_ml: float
    blood_group: str
    donor_id: str
    expiration_date: Optional[datetime]
    status: str = "Active"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        self.blood_group = self.blood_group.strip().upper()
        if self.volume_ml <= 0:
            raise ValueError(f"Aliquot volume must be positive, got {self.volume_ml}")


@dataclass
class ParentBloodUnit:
    """Represents a primary parent blood bag eligible for pediatric splitting."""
    unit_id: str
    blood_group: str
    donor_id: str
    initial_volume_ml: float = 450.0
    available_volume_ml: float = 450.0
    expiration_date: Optional[datetime] = None
    status: str = "Active"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        self.blood_group = self.blood_group.strip().upper()
        if self.initial_volume_ml <= 0:
            raise ValueError(f"Initial volume must be positive, got {self.initial_volume_ml}")
        if self.available_volume_ml < 0:
            raise ValueError(f"Available volume cannot be negative, got {self.available_volume_ml}")


@dataclass
class AliquotSplitResult:
    """Audit payload detailing the outcome of an aliquot split operation."""
    parent_unit_id: str
    initial_parent_volume_ml: float
    remaining_parent_volume_ml: float
    total_volume_split_ml: float
    aliquots_created: List[ChildAliquot]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class AliquotTrackerEngine:
    """Engine managing parent blood units, aliquot splitting, lineage, and volume balance."""

    def __init__(self):
        self._parents: Dict[str, ParentBloodUnit] = {}
        self._aliquots: Dict[str, ChildAliquot] = {}
        self._parent_to_aliquots: Dict[str, List[str]] = {}

    def register_parent_unit(
        self,
        unit_id: str,
        blood_group: str,
        donor_id: str,
        initial_volume_ml: float = 450.0,
        expiration_date: Optional[datetime] = None,
    ) -> ParentBloodUnit:
        """Register a parent blood unit in the inventory."""
        unit_id = unit_id.strip()
        if not unit_id:
            raise ValueError("Parent unit ID cannot be empty.")
        if unit_id in self._parents:
            raise ValueError(f"Parent unit '{unit_id}' is already registered.")

        parent = ParentBloodUnit(
            unit_id=unit_id,
            blood_group=blood_group,
            donor_id=donor_id,
            initial_volume_ml=initial_volume_ml,
            available_volume_ml=initial_volume_ml,
            expiration_date=expiration_date,
        )
        self._parents[unit_id] = parent
        self._parent_to_aliquots[unit_id] = []
        return parent

    def split_parent_unit(
        self,
        parent_unit_id: str,
        aliquot_volumes: List[float],
        custom_aliquot_ids: Optional[List[str]] = None,
    ) -> AliquotSplitResult:
        """Split a parent blood unit into child aliquot units.

        - Creates child aliquot records linked to parent_unit_id.
        - Inherits parent blood group, donor ID, and expiration date across all child aliquots.
        - Reduces available parent unit volume while adding child units to active stock.
        """
        if parent_unit_id not in self._parents:
            raise KeyError(f"Parent unit '{parent_unit_id}' does not exist.")

        parent = self._parents[parent_unit_id]

        if parent.status != "Active":
            raise ValueError(f"Parent unit '{parent_unit_id}' is {parent.status} and cannot be split.")

        if not aliquot_volumes:
            raise ValueError("Aliquot volumes list cannot be empty.")

        for vol in aliquot_volumes:
            if vol <= 0:
                raise ValueError(f"Aliquot volume must be positive, got {vol}")

        total_requested = sum(aliquot_volumes)
        if total_requested > parent.available_volume_ml:
            raise ValueError(
                f"Requested aliquot volume ({total_requested}ml) exceeds "
                f"available parent unit volume ({parent.available_volume_ml}ml)."
            )

        if custom_aliquot_ids and len(custom_aliquot_ids) != len(aliquot_volumes):
            raise ValueError("Length of custom_aliquot_ids must match aliquot_volumes.")

        current_child_count = len(self._parent_to_aliquots[parent_unit_id])
        created_aliquots: List[ChildAliquot] = []

        for i, vol in enumerate(aliquot_volumes, start=1):
            index = current_child_count + i
            aliquot_id = (
                custom_aliquot_ids[i - 1]
                if custom_aliquot_ids
                else f"{parent_unit_id}-ALQ-{index}"
            )
            child = ChildAliquot(
                aliquot_id=aliquot_id,
                parent_unit_id=parent_unit_id,
                aliquot_index=index,
                volume_ml=vol,
                blood_group=parent.blood_group,
                donor_id=parent.donor_id,
                expiration_date=parent.expiration_date,
                status="Active",
            )
            self._aliquots[aliquot_id] = child
            self._parent_to_aliquots[parent_unit_id].append(aliquot_id)
            created_aliquots.append(child)

        # Reduce available volume of parent unit
        parent.available_volume_ml -= total_requested
        if parent.available_volume_ml == 0:
            parent.status = "Depleted"

        return AliquotSplitResult(
            parent_unit_id=parent_unit_id,
            initial_parent_volume_ml=parent.initial_volume_ml,
            remaining_parent_volume_ml=parent.available_volume_ml,
            total_volume_split_ml=total_requested,
            aliquots_created=created_aliquots,
        )

    def get_parent_unit(self, unit_id: str) -> Optional[ParentBloodUnit]:
        """Retrieve parent unit by ID."""
        return self._parents.get(unit_id)

    def get_child_aliquot(self, aliquot_id: str) -> Optional[ChildAliquot]:
        """Retrieve child aliquot by ID."""
        return self._aliquots.get(aliquot_id)

    def get_child_aliquots(self, parent_unit_id: str) -> List[ChildAliquot]:
        """Retrieve all child aliquots derived from a parent unit."""
        aliquot_ids = self._parent_to_aliquots.get(parent_unit_id, [])
        return [self._aliquots[aid] for aid in aliquot_ids]

    def get_active_stock(self, blood_group: Optional[str] = None) -> List[ChildAliquot]:
        """Return all active child aliquots, optionally filtered by blood group."""
        active = [a for a in self._aliquots.values() if a.status == "Active"]
        if blood_group:
            bg_clean = blood_group.strip().upper()
            active = [a for a in active if a.blood_group == bg_clean]
        return active

    def verify_lineage(self, aliquot_id: str) -> Dict[str, Any]:
        """Verify complete lineage of a child aliquot against its parent unit."""
        if aliquot_id not in self._aliquots:
            raise KeyError(f"Aliquot '{aliquot_id}' not found.")

        aliquot = self._aliquots[aliquot_id]
        parent = self._parents.get(aliquot.parent_unit_id)

        if not parent:
            return {
                "aliquot_id": aliquot_id,
                "parent_unit_id": aliquot.parent_unit_id,
                "is_valid": False,
                "reason": "Parent unit does not exist.",
            }

        blood_group_matches = aliquot.blood_group == parent.blood_group
        donor_matches = aliquot.donor_id == parent.donor_id
        expiration_matches = aliquot.expiration_date == parent.expiration_date

        is_valid = blood_group_matches and donor_matches and expiration_matches

        return {
            "aliquot_id": aliquot_id,
            "parent_unit_id": parent.unit_id,
            "is_valid": is_valid,
            "blood_group_matches": blood_group_matches,
            "donor_matches": donor_matches,
            "expiration_matches": expiration_matches,
            "parent_details": {
                "unit_id": parent.unit_id,
                "blood_group": parent.blood_group,
                "donor_id": parent.donor_id,
                "initial_volume_ml": parent.initial_volume_ml,
                "available_volume_ml": parent.available_volume_ml,
                "expiration_date": parent.expiration_date.isoformat() if parent.expiration_date else None,
                "status": parent.status,
            },
            "aliquot_details": {
                "aliquot_id": aliquot.aliquot_id,
                "aliquot_index": aliquot.aliquot_index,
                "volume_ml": aliquot.volume_ml,
                "blood_group": aliquot.blood_group,
                "donor_id": aliquot.donor_id,
                "expiration_date": aliquot.expiration_date.isoformat() if aliquot.expiration_date else None,
                "status": aliquot.status,
            },
        }

    def verify_volume_balance(self, parent_unit_id: str) -> Dict[str, Any]:
        """Verify mathematical volume balance: parent_initial == available + sum(child_aliquots)."""
        if parent_unit_id not in self._parents:
            raise KeyError(f"Parent unit '{parent_unit_id}' not found.")

        parent = self._parents[parent_unit_id]
        child_aliquots = self.get_child_aliquots(parent_unit_id)
        aliquoted_volume = sum(c.volume_ml for c in child_aliquots)
        total_accounted_volume = parent.available_volume_ml + aliquoted_volume

        difference = round(abs(total_accounted_volume - parent.initial_volume_ml), 6)
        is_balanced = difference == 0.0

        return {
            "parent_unit_id": parent_unit_id,
            "initial_volume_ml": parent.initial_volume_ml,
            "available_volume_ml": parent.available_volume_ml,
            "aliquoted_volume_ml": aliquoted_volume,
            "child_units_count": len(child_aliquots),
            "total_accounted_volume_ml": total_accounted_volume,
            "volume_difference_ml": difference,
            "is_balanced": is_balanced,
        }
