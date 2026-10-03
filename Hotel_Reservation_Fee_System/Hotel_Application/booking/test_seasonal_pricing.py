"""Unit tests for Dynamic Room Rate Seasonal Surge Calculator & Weekend Surcharge Module (CR-854)."""

import os
import sys
from datetime import date
import pytest

_app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _app_root not in sys.path:
    sys.path.insert(0, _app_root)

from booking.seasonal_pricing import (
    DynamicRoomPricingEngine,
    DailyRateBreakdown,
    ReservationQuote,
    DEFAULT_PEAK_SURGE_MULTIPLIER,
    DEFAULT_WEEKEND_MULTIPLIER,
)


@pytest.fixture
def engine():
    """Returns a freshly initialized DynamicRoomPricingEngine."""
    return DynamicRoomPricingEngine()


def test_regular_weekday_pricing(engine):
    """Regular non-peak weekday stay (e.g. Wednesday in October) has 1.0x multiplier."""
    # Oct 14, 2026 is a Wednesday (non-peak, non-weekend)
    stay_date = date(2026, 10, 14)
    daily = engine.calculate_daily_rate(stay_date, base_rate=100.0)

    assert daily.base_rate == 100.0
    assert daily.is_peak_season is False
    assert daily.seasonal_multiplier == 1.0
    assert daily.is_weekend is False
    assert daily.weekend_multiplier == 1.0
    assert daily.effective_daily_rate == 100.0


def test_peak_season_weekday_pricing(engine):
    """Peak season weekday stay applies 1.25x surge multiplier."""
    # July 15, 2026 is a Wednesday in summer peak season
    stay_date = date(2026, 7, 15)
    daily = engine.calculate_daily_rate(stay_date, base_rate=100.0)

    assert daily.is_peak_season is True
    assert daily.seasonal_multiplier == 1.25
    assert daily.is_weekend is False
    assert daily.weekend_multiplier == 1.0
    assert daily.effective_daily_rate == 125.0


def test_regular_weekend_pricing(engine):
    """Regular season Friday/Saturday night stay applies 1.15x weekend multiplier."""
    # Oct 16, 2026 is Friday; Oct 17, 2026 is Saturday
    friday = date(2026, 10, 16)
    saturday = date(2026, 10, 17)

    fri_rate = engine.calculate_daily_rate(friday, base_rate=100.0)
    assert fri_rate.is_peak_season is False
    assert fri_rate.is_weekend is True
    assert fri_rate.weekend_multiplier == 1.15
    assert fri_rate.effective_daily_rate == 115.0

    sat_rate = engine.calculate_daily_rate(saturday, base_rate=100.0)
    assert sat_rate.is_weekend is True
    assert sat_rate.effective_daily_rate == 115.0


def test_peak_season_weekend_combined_multipliers(engine):
    """Combined peak season and weekend stay multiplies both: 1.25 * 1.15 = 1.4375x."""
    # July 17, 2026 is Friday during Summer peak season
    peak_friday = date(2026, 7, 17)
    daily = engine.calculate_daily_rate(peak_friday, base_rate=200.0)

    assert daily.is_peak_season is True
    assert daily.seasonal_multiplier == 1.25
    assert daily.is_weekend is True
    assert daily.weekend_multiplier == 1.15

    # 200 * 1.25 * 1.15 = 200 * 1.4375 = 287.50
    assert daily.effective_daily_rate == 287.50


def test_sunday_night_is_regular_weekday(engine):
    """Sunday night stay is treated as weekday (not weekend surcharge)."""
    # Oct 18, 2026 is Sunday
    sunday = date(2026, 10, 18)
    daily = engine.calculate_daily_rate(sunday, base_rate=100.0)

    assert daily.is_weekend is False
    assert daily.weekend_multiplier == 1.0
    assert daily.effective_daily_rate == 100.0


def test_multi_day_booking_combined_calculation(engine):
    """Multi-day stay across Thursday, Friday, and Saturday nights correctly calculates total quote."""
    # Oct 15, 2026 (Thu) -> Oct 18, 2026 (Sun checkout) = 3 nights (Thu, Fri, Sat)
    # Thu: 100.0, Fri: 115.0, Sat: 115.0 -> Total = 330.0
    quote = engine.calculate_reservation_quote(
        check_in="2026-10-15",
        check_out="2026-10-18",
        base_rate=100.0,
    )

    assert quote.total_nights == 3
    assert quote.base_rate_per_night == 100.0
    assert quote.total_base_cost == 300.0
    assert quote.total_effective_cost == 330.0
    assert quote.total_surge_amount == 30.0
    assert quote.average_nightly_rate == 110.0
    assert len(quote.daily_breakdown) == 3


def test_multi_day_summer_peak_booking(engine):
    """Multi-day stay during Summer peak season across weekdays and weekend."""
    # July 16, 2026 (Thu) -> July 19, 2026 (Sun) = 3 nights
    # Thu: 100 * 1.25 = 125.0
    # Fri: 100 * 1.25 * 1.15 = 143.75
    # Sat: 100 * 1.25 * 1.15 = 143.75
    # Total = 125.0 + 143.75 + 143.75 = 412.50
    quote = engine.calculate_reservation_quote(
        check_in=date(2026, 7, 16),
        check_out=date(2026, 7, 19),
        base_rate=100.0,
    )

    assert quote.total_nights == 3
    assert quote.total_effective_cost == 412.50
    assert quote.total_surge_amount == 112.50
    assert quote.average_nightly_rate == 137.50


def test_custom_peak_range_addition(engine):
    """Allows adding custom festival or event peak date ranges."""
    event_start = date(2026, 11, 10)
    event_end = date(2026, 11, 12)
    engine.add_peak_date_range(event_start, event_end)

    # Nov 11 is now peak
    daily = engine.calculate_daily_rate(date(2026, 11, 11), base_rate=100.0)
    assert daily.is_peak_season is True
    assert daily.seasonal_multiplier == 1.25


def test_invalid_parameters_validation(engine):
    """Validates negative rates, checkout before checkin, or non-positive multipliers."""
    with pytest.raises(ValueError, match="negative"):
        engine.calculate_daily_rate(date(2026, 10, 1), base_rate=-50.0)

    with pytest.raises(ValueError, match="strictly after"):
        engine.calculate_reservation_quote(date(2026, 10, 10), date(2026, 10, 10), 100.0)

    with pytest.raises(ValueError, match="strictly after"):
        engine.calculate_reservation_quote(date(2026, 10, 15), date(2026, 10, 10), 100.0)

    with pytest.raises(ValueError, match="positive"):
        DynamicRoomPricingEngine(peak_surge_multiplier=-1.2)


def test_quote_serialization(engine):
    """Verifies dictionary conversion of reservation quote."""
    quote = engine.calculate_reservation_quote("2026-10-15", "2026-10-17", 120.0)
    data = quote.to_dict()

    assert data["total_nights"] == 2
    assert "daily_breakdown" in data
    assert len(data["daily_breakdown"]) == 2
    assert data["daily_breakdown"][0]["day_name"] == "Thursday"
