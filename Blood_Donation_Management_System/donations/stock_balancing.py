"""Regional Blood Bank Stock Inventory Balancing Engine (CR-752).

Calculates facility target reserve stock from average weekly consumption,
detects surplus (>150% target) and deficit (<50% target) supply conditions,
and computes inter-facility blood inventory transfer recommendations.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import math
from typing import Any, Dict, List, Optional


@dataclass
class FacilityStock:
    """Represents blood inventory and consumption metrics for a medical facility."""
    facility_id: str
    facility_name: str
    blood_group: str
    current_stock: int
    avg_weekly_consumption: float
    target_reserve_stock: int = 0

    def __post_init__(self):
        self.blood_group = self.blood_group.strip().upper()
        if self.target_reserve_stock <= 0:
            self.target_reserve_stock = self.calculate_target_stock()

    def calculate_target_stock(self, reserve_buffer_weeks: float = 1.0) -> int:
        """Calculate target reserve stock based on average weekly consumption.

        Target stock = ceil(avg_weekly_consumption * reserve_buffer_weeks).
        Ensures a minimum of 1 unit if consumption > 0.
        """
        if self.avg_weekly_consumption <= 0:
            return 0
        calculated = math.ceil(self.avg_weekly_consumption * reserve_buffer_weeks)
        return max(1, calculated)

    @property
    def surplus_threshold(self) -> float:
        """Surplus threshold (>150% of target reserve stock)."""
        return 1.5 * self.target_reserve_stock

    @property
    def deficit_threshold(self) -> float:
        """Deficit threshold (<50% of target reserve stock)."""
        return 0.5 * self.target_reserve_stock

    @property
    def is_surplus(self) -> bool:
        """True if current stock exceeds 150% of target reserve."""
        return self.current_stock > self.surplus_threshold

    @property
    def is_deficit(self) -> bool:
        """True if current stock falls below 50% of target reserve."""
        return self.current_stock < self.deficit_threshold

    @property
    def transferable_surplus(self) -> int:
        """Units available to transfer without dropping facility below target reserve."""
        if not self.is_surplus:
            return 0
        return max(0, self.current_stock - self.target_reserve_stock)

    @property
    def deficit_amount(self) -> int:
        """Units required to restore facility to target reserve stock."""
        if not self.is_deficit:
            return 0
        return max(0, self.target_reserve_stock - self.current_stock)


@dataclass
class TransferRecommendation:
    """Represents an automated transfer recommendation between two facilities."""
    from_facility_id: str
    from_facility_name: str
    to_facility_id: str
    to_facility_name: str
    blood_group: str
    units: int
    rationale: str
    recommended_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "from_facility_id": self.from_facility_id,
            "from_facility_name": self.from_facility_name,
            "to_facility_id": self.to_facility_id,
            "to_facility_name": self.to_facility_name,
            "blood_group": self.blood_group,
            "units": self.units,
            "rationale": self.rationale,
            "recommended_at": self.recommended_at.isoformat(),
        }


class RegionalStockBalancingEngine:
    """Engine analyzing regional blood inventory and generating rebalancing transfers."""

    def __init__(self):
        # facility_id -> FacilityStock
        self._facilities: Dict[str, FacilityStock] = {}
        self._transfer_history: List[TransferRecommendation] = []

    def register_facility_stock(self, facility: FacilityStock) -> None:
        """Add or update facility stock in the regional network."""
        key = f"{facility.facility_id}:{facility.blood_group}"
        self._facilities[key] = facility

    def get_facility_stock(self, facility_id: str, blood_group: str) -> Optional[FacilityStock]:
        """Retrieve facility stock record by ID and blood group."""
        key = f"{facility_id}:{blood_group.strip().upper()}"
        return self._facilities.get(key)

    def calculate_facility_target_stock(
        self,
        avg_weekly_consumption: float,
        buffer_weeks: float = 1.0
    ) -> int:
        """Utility calculating target reserve stock for consumption."""
        if avg_weekly_consumption <= 0:
            return 0
        return max(1, math.ceil(avg_weekly_consumption * buffer_weeks))

    def identify_surplus_facilities(self, blood_group: Optional[str] = None) -> List[FacilityStock]:
        """Find all facilities with current_stock > 150% of target reserve stock."""
        surplus = []
        bg_filter = blood_group.strip().upper() if blood_group else None
        for record in self._facilities.values():
            if bg_filter and record.blood_group != bg_filter:
                continue
            if record.is_surplus:
                surplus.append(record)
        # Order by highest transferable surplus descending
        surplus.sort(key=lambda f: f.transferable_surplus, reverse=True)
        return surplus

    def identify_deficit_facilities(self, blood_group: Optional[str] = None) -> List[FacilityStock]:
        """Find all facilities with current_stock < 50% of target reserve stock."""
        deficits = []
        bg_filter = blood_group.strip().upper() if blood_group else None
        for record in self._facilities.values():
            if bg_filter and record.blood_group != bg_filter:
                continue
            if record.is_deficit:
                deficits.append(record)
        # Order by highest deficit amount descending
        deficits.sort(key=lambda f: f.deficit_amount, reverse=True)
        return deficits

    def generate_transfer_recommendations(
        self,
        blood_group: Optional[str] = None
    ) -> List[TransferRecommendation]:
        """Generate transfer orders routing surplus blood to deficit facilities.

        Pairs facilities matching the same blood group, reducing regional deficits
        while preserving donor facility reserve targets.
        """
        recommendations: List[TransferRecommendation] = []

        # Group facilities by blood group
        grouped_by_bg: Dict[str, List[FacilityStock]] = {}
        for record in self._facilities.values():
            if blood_group and record.blood_group != blood_group.strip().upper():
                continue
            grouped_by_bg.setdefault(record.blood_group, []).append(record)

        for bg, facilities in grouped_by_bg.items():
            # Track working surplus and deficit levels
            surplus_list = [f for f in facilities if f.is_surplus]
            deficit_list = [f for f in facilities if f.is_deficit]

            surplus_pools = {f.facility_id: f.transferable_surplus for f in surplus_list}
            deficit_needs = {f.facility_id: f.deficit_amount for f in deficit_list}

            surplus_map = {f.facility_id: f for f in surplus_list}
            deficit_map = {f.facility_id: f for f in deficit_list}

            for def_id, need in deficit_needs.items():
                def_facility = deficit_map[def_id]
                remaining_need = need

                for sur_id, available in list(surplus_pools.items()):
                    if remaining_need <= 0:
                        break
                    if available <= 0:
                        continue

                    sur_facility = surplus_map[sur_id]
                    transfer_qty = min(available, remaining_need)

                    if transfer_qty > 0:
                        recommendation = TransferRecommendation(
                            from_facility_id=sur_facility.facility_id,
                            from_facility_name=sur_facility.facility_name,
                            to_facility_id=def_facility.facility_id,
                            to_facility_name=def_facility.facility_name,
                            blood_group=bg,
                            units=transfer_qty,
                            rationale=(
                                f"Rebalance regional {bg} supply: {sur_facility.facility_name} "
                                f"has {sur_facility.current_stock} units (>150% of target {sur_facility.target_reserve_stock}); "
                                f"{def_facility.facility_name} has {def_facility.current_stock} units "
                                f"(<50% of target {def_facility.target_reserve_stock})."
                            ),
                        )
                        recommendations.append(recommendation)
                        self._transfer_history.append(recommendation)

                        surplus_pools[sur_id] -= transfer_qty
                        remaining_need -= transfer_qty

        return recommendations

    @property
    def transfer_history(self) -> List[TransferRecommendation]:
        return list(self._transfer_history)
