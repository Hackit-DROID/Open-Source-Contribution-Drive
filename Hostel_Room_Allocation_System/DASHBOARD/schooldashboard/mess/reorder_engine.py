"""Hostel Mess Supply Reorder Point Engine & Automated Inventory Depletion Predictor (CR-852).

Predicts mess food and supply inventory stock depletion rates based on enrolled student
headcount, calculates daily consumption rates (daily_per_student * student_count),
and flags automated reorder purchase warnings when remaining stock drops below 3.0 days of supply.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import math
from typing import Any, Dict, List, Optional
import uuid


REORDER_THRESHOLD_DAYS: float = 3.0


@dataclass
class MessSupplyItem:
    """Represents a food supply item in the hostel mess inventory."""
    item_id: str
    name: str
    unit: str
    current_stock: float
    daily_per_student: float
    safety_buffer_days: float = REORDER_THRESHOLD_DAYS

    def __post_init__(self):
        self.item_id = self.item_id.strip()
        self.name = self.name.strip()
        if self.current_stock < 0:
            raise ValueError(f"Current stock cannot be negative, got {self.current_stock}")
        if self.daily_per_student < 0:
            raise ValueError(f"Daily consumption per student cannot be negative, got {self.daily_per_student}")


@dataclass
class ReorderAlert:
    """Structured alert generated when supply item drops below the reorder threshold."""
    alert_id: str
    item_id: str
    item_name: str
    current_stock: float
    student_count: int
    daily_consumption: float
    days_left: float
    reorder_threshold_days: float
    severity: str
    suggested_order_quantity: float
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "item_id": self.item_id,
            "item_name": self.item_name,
            "current_stock": self.current_stock,
            "student_count": self.student_count,
            "daily_consumption": self.daily_consumption,
            "days_left": self.days_left,
            "reorder_threshold_days": self.reorder_threshold_days,
            "severity": self.severity,
            "suggested_order_quantity": self.suggested_order_quantity,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class DepletionPredictionResult:
    """Detailed depletion rate and reorder status for a single supply item."""
    item_id: str
    item_name: str
    current_stock: float
    student_count: int
    daily_per_student: float
    daily_consumption: float
    days_left: float
    needs_reorder: bool
    alert: Optional[ReorderAlert] = None


class MessInventoryDepletionEngine:
    """Engine calculating stock consumption rates, predicting depletion days, and generating reorder alerts."""

    def __init__(self, reorder_threshold_days: float = REORDER_THRESHOLD_DAYS):
        self.reorder_threshold_days = float(reorder_threshold_days)

    def calculate_daily_consumption(self, daily_per_student: float, student_count: int) -> float:
        """Calculate daily stock consumption rate = daily_per_student * student_count.

        Acceptance criterion:
        Calculates daily stock consumption rate = daily_per_student * student_count.
        """
        if daily_per_student < 0:
            raise ValueError(f"daily_per_student cannot be negative, got {daily_per_student}")
        if student_count < 0:
            raise ValueError(f"student_count cannot be negative, got {student_count}")
        return round(float(daily_per_student * student_count), 4)

    def calculate_days_left(self, current_stock: float, daily_consumption: float) -> float:
        """Compute days of supply remaining: current_stock / daily_consumption."""
        if current_stock < 0:
            raise ValueError(f"current_stock cannot be negative, got {current_stock}")
        if daily_consumption <= 0:
            return float("inf")
        return round(float(current_stock / daily_consumption), 2)

    def evaluate_item(
        self,
        item: MessSupplyItem,
        student_count: int,
        target_stock_days: float = 7.0,
    ) -> DepletionPredictionResult:
        """Evaluate inventory depletion and create reorder alert if below threshold."""
        daily_consumption = self.calculate_daily_consumption(
            daily_per_student=item.daily_per_student,
            student_count=student_count,
        )
        days_left = self.calculate_days_left(
            current_stock=item.current_stock,
            daily_consumption=daily_consumption,
        )

        threshold = item.safety_buffer_days or self.reorder_threshold_days
        # Flags reorder warning when current_stock / daily_consumption < 3.0 days
        needs_reorder = days_left < threshold

        alert: Optional[ReorderAlert] = None
        if needs_reorder:
            severity = "CRITICAL" if days_left < 1.0 else "WARNING"
            suggested_reorder = max(
                0.0,
                round((target_stock_days * daily_consumption) - item.current_stock, 2),
            )
            alert = ReorderAlert(
                alert_id=f"ALT-{uuid.uuid4().hex[:8].upper()}",
                item_id=item.item_id,
                item_name=item.name,
                current_stock=item.current_stock,
                student_count=student_count,
                daily_consumption=daily_consumption,
                days_left=days_left,
                reorder_threshold_days=threshold,
                severity=severity,
                suggested_order_quantity=suggested_reorder,
            )

        return DepletionPredictionResult(
            item_id=item.item_id,
            item_name=item.name,
            current_stock=item.current_stock,
            student_count=student_count,
            daily_per_student=item.daily_per_student,
            daily_consumption=daily_consumption,
            days_left=days_left,
            needs_reorder=needs_reorder,
            alert=alert,
        )

    def evaluate_inventory(
        self,
        items: List[MessSupplyItem],
        student_count: int,
        target_stock_days: float = 7.0,
    ) -> List[DepletionPredictionResult]:
        """Evaluate all inventory items against active student headcount."""
        return [self.evaluate_item(item, student_count, target_stock_days) for item in items]

    def get_reorder_alerts(
        self,
        items: List[MessSupplyItem],
        student_count: int,
        target_stock_days: float = 7.0,
    ) -> List[ReorderAlert]:
        """Return list of active reorder alerts for all items below threshold (< 3.0 days)."""
        results = self.evaluate_inventory(items, student_count, target_stock_days)
        return [res.alert for res in results if res.alert is not None]
