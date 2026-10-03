"""Donor Retention Rate & Re-Donation Frequency Analytics Dashboard Engine (CR-702).

Computes blood donor engagement analytics including repeat donor ratio,
average days between consecutive donations, churn rate, and distribution metrics.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Dict, Iterable, List, Optional, Union


@dataclass
class DonorRetentionMetrics:
    """Summary metrics of donor retention and re-donation frequency."""
    total_donors: int
    repeat_donors: int
    single_time_donors: int
    repeat_donor_ratio: float
    churn_rate: float
    total_donations: int
    average_days_between_donations: float
    per_donor_intervals: Dict[str, List[int]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_donors": self.total_donors,
            "repeat_donors": self.repeat_donors,
            "single_time_donors": self.single_time_donors,
            "repeat_donor_ratio": round(self.repeat_donor_ratio, 2),
            "churn_rate": round(self.churn_rate, 2),
            "total_donations": self.total_donations,
            "average_days_between_donations": round(self.average_days_between_donations, 2),
            "per_donor_intervals": self.per_donor_intervals,
        }


class DonorRetentionAnalyticsEngine:
    """Engine calculating donor retention, repeat donation ratio, and frequency metrics."""

    def __init__(self):
        # donor_id -> list of donation date objects
        self._donations: Dict[str, List[date]] = {}

    @staticmethod
    def calculate_repeat_donor_ratio(repeat_donors: int, total_donors: int) -> float:
        """Calculate repeat donor ratio formula: (repeat_donors / total_donors) * 100.

        Args:
            repeat_donors: Count of donors with >= 2 donations.
            total_donors: Total unique donors.

        Returns:
            Percentage of repeat donors (0.0 to 100.0). Returns 0.0 if total_donors is 0.
        """
        if total_donors < 0 or repeat_donors < 0:
            raise ValueError("Donor counts cannot be negative.")
        if repeat_donors > total_donors:
            raise ValueError("Repeat donors cannot exceed total donors.")
        if total_donors == 0:
            return 0.0
        return (repeat_donors / total_donors) * 100.0

    @staticmethod
    def _normalize_date(d: Union[date, datetime, str]) -> date:
        """Convert input date/datetime/string to standard date object."""
        if isinstance(d, datetime):
            return d.date()
        elif isinstance(d, date):
            return d
        elif isinstance(d, str):
            # Parse ISO or YYYY-MM-DD
            clean_str = d.split("T")[0].split(" ")[0].strip()
            return datetime.strptime(clean_str, "%Y-%m-%d").date()
        raise TypeError(f"Unsupported date format: {type(d)}")

    def record_donation(
        self,
        donor_id: Union[str, int],
        donation_date: Union[date, datetime, str],
    ) -> None:
        """Register a donation event for a donor."""
        key = str(donor_id).strip()
        norm_date = self._normalize_date(donation_date)
        self._donations.setdefault(key, []).append(norm_date)

    def load_donations(
        self,
        records: Iterable[Union[Dict[str, Any], Any]],
        donor_id_field: str = "donor_id",
        date_field: str = "date",
    ) -> None:
        """Bulk load donation records from dictionaries or model objects."""
        for item in records:
            if isinstance(item, dict):
                donor_id = item.get(donor_id_field)
                d_date = item.get(date_field)
            else:
                donor_id = getattr(item, donor_id_field, None)
                if donor_id is None and hasattr(item, "donor"):
                    donor_id = getattr(item.donor, "id", str(item.donor))
                d_date = getattr(item, date_field, None)

            if donor_id is not None and d_date is not None:
                self.record_donation(donor_id, d_date)

    def compute_donor_intervals(self, donor_id: Union[str, int]) -> List[int]:
        """Compute days between consecutive donations for a specific donor."""
        key = str(donor_id).strip()
        dates = self._donations.get(key, [])
        if len(dates) < 2:
            return []

        sorted_dates = sorted(dates)
        intervals = []
        for i in range(1, len(sorted_dates)):
            diff = (sorted_dates[i] - sorted_dates[i - 1]).days
            intervals.append(diff)
        return intervals

    def compute_metrics(self) -> DonorRetentionMetrics:
        """Compute comprehensive donor retention metrics across all loaded records."""
        total_donors = len(self._donations)
        if total_donors == 0:
            return DonorRetentionMetrics(
                total_donors=0,
                repeat_donors=0,
                single_time_donors=0,
                repeat_donor_ratio=0.0,
                churn_rate=0.0,
                total_donations=0,
                average_days_between_donations=0.0,
                per_donor_intervals={},
            )

        repeat_donors = 0
        single_time_donors = 0
        total_donations = 0
        all_intervals: List[int] = []
        per_donor_intervals: Dict[str, List[int]] = {}

        for donor_id, dates in self._donations.items():
            count = len(dates)
            total_donations += count
            if count >= 2:
                repeat_donors += 1
                intervals = self.compute_donor_intervals(donor_id)
                per_donor_intervals[donor_id] = intervals
                all_intervals.extend(intervals)
            else:
                single_time_donors += 1

        repeat_ratio = self.calculate_repeat_donor_ratio(repeat_donors, total_donors)
        churn_rate = 100.0 - repeat_ratio if total_donors > 0 else 0.0

        if all_intervals:
            avg_interval = sum(all_intervals) / len(all_intervals)
        else:
            avg_interval = 0.0

        return DonorRetentionMetrics(
            total_donors=total_donors,
            repeat_donors=repeat_donors,
            single_time_donors=single_time_donors,
            repeat_donor_ratio=repeat_ratio,
            churn_rate=churn_rate,
            total_donations=total_donations,
            average_days_between_donations=avg_interval,
            per_donor_intervals=per_donor_intervals,
        )
