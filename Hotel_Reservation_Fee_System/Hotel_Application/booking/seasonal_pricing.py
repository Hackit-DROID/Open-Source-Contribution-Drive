"""Dynamic Room Rate Seasonal Surge Calculator & Weekend Surcharge Module (CR-854).

Calculates dynamic room pricing by applying configurable seasonal surge multipliers
(1.25x for peak dates) and weekend surcharges (1.15x for Friday/Saturday stays)
across single and multi-day hotel reservations.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union


DEFAULT_PEAK_SURGE_MULTIPLIER: float = 1.25
DEFAULT_WEEKEND_MULTIPLIER: float = 1.15

# Standard weekend nights: Friday (4) and Saturday (5) in Python weekday()
WEEKEND_DAYS = {4, 5}


@dataclass
class DailyRateBreakdown:
    """Detailed price calculation for an individual night stay."""
    stay_date: date
    day_name: str
    base_rate: float
    is_peak_season: bool
    seasonal_multiplier: float
    is_weekend: bool
    weekend_multiplier: float
    effective_daily_rate: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stay_date": self.stay_date.isoformat(),
            "day_name": self.day_name,
            "base_rate": round(self.base_rate, 2),
            "is_peak_season": self.is_peak_season,
            "seasonal_multiplier": self.seasonal_multiplier,
            "is_weekend": self.is_weekend,
            "weekend_multiplier": self.weekend_multiplier,
            "effective_daily_rate": round(self.effective_daily_rate, 2),
        }


@dataclass
class ReservationQuote:
    """Aggregated dynamic pricing quote for a multi-day hotel booking."""
    check_in: date
    check_out: date
    total_nights: int
    base_rate_per_night: float
    total_base_cost: float
    total_effective_cost: float
    total_surge_amount: float
    average_nightly_rate: float
    daily_breakdown: List[DailyRateBreakdown] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "check_in": self.check_in.isoformat(),
            "check_out": self.check_out.isoformat(),
            "total_nights": self.total_nights,
            "base_rate_per_night": round(self.base_rate_per_night, 2),
            "total_base_cost": round(self.total_base_cost, 2),
            "total_effective_cost": round(self.total_effective_cost, 2),
            "total_surge_amount": round(self.total_surge_amount, 2),
            "average_nightly_rate": round(self.average_nightly_rate, 2),
            "daily_breakdown": [d.to_dict() for d in self.daily_breakdown],
        }


class DynamicRoomPricingEngine:
    """Engine applying seasonal and weekend multipliers to hotel room rates."""

    def __init__(
        self,
        peak_surge_multiplier: float = DEFAULT_PEAK_SURGE_MULTIPLIER,
        weekend_multiplier: float = DEFAULT_WEEKEND_MULTIPLIER,
    ):
        if peak_surge_multiplier <= 0:
            raise ValueError("Peak surge multiplier must be positive.")
        if weekend_multiplier <= 0:
            raise ValueError("Weekend multiplier must be positive.")

        self.peak_surge_multiplier = float(peak_surge_multiplier)
        self.weekend_multiplier = float(weekend_multiplier)
        # List of (start_date, end_date) tuples
        self._peak_ranges: List[Tuple[date, date]] = []
        # Annual recurring peak periods: (start_month, start_day, end_month, end_day)
        self._annual_peak_periods: List[Tuple[int, int, int, int]] = [
            (6, 1, 8, 31),    # Summer peak: June 1 to August 31
            (12, 15, 12, 31), # Winter holidays: Dec 15 to Dec 31
            (1, 1, 1, 5),     # New Year peak: Jan 1 to Jan 5
        ]

    def add_peak_date_range(self, start_date: date, end_date: date) -> None:
        """Add a specific date range as peak season."""
        if start_date > end_date:
            raise ValueError(f"start_date ({start_date}) cannot be after end_date ({end_date})")
        self._peak_ranges.append((start_date, end_date))

    def add_annual_peak_period(
        self,
        start_month: int,
        start_day: int,
        end_month: int,
        end_day: int,
    ) -> None:
        """Add an annually recurring peak season calendar window."""
        self._annual_peak_periods.append((start_month, start_day, end_month, end_day))

    def is_peak_date(self, stay_date: date) -> bool:
        """Determine if a given date falls within any configured peak season."""
        # 1. Check explicit date ranges
        for start, end in self._peak_ranges:
            if start <= stay_date <= end:
                return True

        # 2. Check annual recurring periods
        m, d = stay_date.month, stay_date.day
        for s_m, s_d, e_m, e_d in self._annual_peak_periods:
            if s_m <= e_m:
                if (m > s_m or (m == s_m and d >= s_d)) and (m < e_m or (m == e_m and d <= e_d)):
                    return True
            else:
                # Wrap-around year range (e.g. Dec to Jan)
                if (m > s_m or (m == s_m and d >= s_d)) or (m < e_m or (m == e_m and d <= e_d)):
                    return True

        return False

    @staticmethod
    def is_weekend_date(stay_date: date) -> bool:
        """Determine if a night stay is a weekend night (Friday or Saturday)."""
        return stay_date.weekday() in WEEKEND_DAYS

    def calculate_daily_rate(self, stay_date: date, base_rate: float) -> DailyRateBreakdown:
        """Calculate effective rate for an individual night stay."""
        if base_rate < 0:
            raise ValueError("Base room rate cannot be negative.")

        is_peak = self.is_peak_date(stay_date)
        is_wknd = self.is_weekend_date(stay_date)

        season_mult = self.peak_surge_multiplier if is_peak else 1.0
        wknd_mult = self.weekend_multiplier if is_wknd else 1.0

        # Effective daily rate = base_rate * seasonal_factor * weekend_factor
        effective_rate = round(base_rate * season_mult * wknd_mult, 2)

        return DailyRateBreakdown(
            stay_date=stay_date,
            day_name=stay_date.strftime("%A"),
            base_rate=float(base_rate),
            is_peak_season=is_peak,
            seasonal_multiplier=season_mult,
            is_weekend=is_wknd,
            weekend_multiplier=wknd_mult,
            effective_daily_rate=effective_rate,
        )

    def calculate_reservation_quote(
        self,
        check_in: Union[date, str],
        check_out: Union[date, str],
        base_rate: float,
    ) -> ReservationQuote:
        """Calculate complete multi-day dynamic booking pricing quote."""
        if isinstance(check_in, str):
            check_in = datetime.strptime(check_in.split("T")[0], "%Y-%m-%d").date()
        if isinstance(check_out, str):
            check_out = datetime.strptime(check_out.split("T")[0], "%Y-%m-%d").date()

        if check_out <= check_in:
            raise ValueError(f"check_out date ({check_out}) must be strictly after check_in date ({check_in})")
        if base_rate < 0:
            raise ValueError("Base room rate cannot be negative.")

        total_nights = (check_out - check_in).days
        daily_breakdown: List[DailyRateBreakdown] = []

        curr = check_in
        while curr < check_out:
            daily = self.calculate_daily_rate(curr, base_rate)
            daily_breakdown.append(daily)
            curr += timedelta(days=1)

        total_base = round(base_rate * total_nights, 2)
        total_effective = round(sum(d.effective_daily_rate for d in daily_breakdown), 2)
        total_surge = round(total_effective - total_base, 2)
        avg_nightly = round(total_effective / total_nights, 2) if total_nights > 0 else 0.0

        return ReservationQuote(
            check_in=check_in,
            check_out=check_out,
            total_nights=total_nights,
            base_rate_per_night=float(base_rate),
            total_base_cost=total_base,
            total_effective_cost=total_effective,
            total_surge_amount=total_surge,
            average_nightly_rate=avg_nightly,
            daily_breakdown=daily_breakdown,
        )
