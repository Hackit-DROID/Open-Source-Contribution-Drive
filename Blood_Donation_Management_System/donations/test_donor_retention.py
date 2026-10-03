"""Unit tests for Donor Retention Rate & Re-Donation Frequency Analytics Dashboard (CR-702)."""

import os
import sys
from datetime import date, datetime
import pytest

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from donations.donor_retention import (
    DonorRetentionAnalyticsEngine,
    DonorRetentionMetrics,
)


@pytest.fixture
def engine():
    """Returns a freshly initialized DonorRetentionAnalyticsEngine."""
    return DonorRetentionAnalyticsEngine()


def test_repeat_donor_ratio_formula():
    """Verifies repeat donor ratio calculation: (repeat_donors / total_donors) * 100."""
    # 5 repeat donors out of 20 total donors = 25.0%
    assert DonorRetentionAnalyticsEngine.calculate_repeat_donor_ratio(5, 20) == 25.0
    # 10 repeat donors out of 10 total donors = 100.0%
    assert DonorRetentionAnalyticsEngine.calculate_repeat_donor_ratio(10, 10) == 100.0
    # 0 repeat donors out of 15 total donors = 0.0%
    assert DonorRetentionAnalyticsEngine.calculate_repeat_donor_ratio(0, 15) == 0.0
    # 0 total donors returns 0.0 without division by zero
    assert DonorRetentionAnalyticsEngine.calculate_repeat_donor_ratio(0, 0) == 0.0


def test_repeat_donor_ratio_validation():
    """Rejects negative values or repeat donors exceeding total donors."""
    with pytest.raises(ValueError, match="negative"):
        DonorRetentionAnalyticsEngine.calculate_repeat_donor_ratio(-1, 10)
    with pytest.raises(ValueError, match="exceed"):
        DonorRetentionAnalyticsEngine.calculate_repeat_donor_ratio(15, 10)


def test_empty_engine_metrics(engine):
    """Empty engine returns zeroed metrics without crashing."""
    metrics = engine.compute_metrics()
    assert metrics.total_donors == 0
    assert metrics.repeat_donors == 0
    assert metrics.single_time_donors == 0
    assert metrics.repeat_donor_ratio == 0.0
    assert metrics.churn_rate == 0.0
    assert metrics.total_donations == 0
    assert metrics.average_days_between_donations == 0.0


def test_single_time_donors_only(engine):
    """Dataset with only one-time donors produces 0% repeat ratio and 100% churn rate."""
    engine.record_donation("D1", date(2026, 1, 10))
    engine.record_donation("D2", date(2026, 2, 15))
    engine.record_donation("D3", date(2026, 3, 20))

    metrics = engine.compute_metrics()
    assert metrics.total_donors == 3
    assert metrics.repeat_donors == 0
    assert metrics.single_time_donors == 3
    assert metrics.repeat_donor_ratio == 0.0
    assert metrics.churn_rate == 100.0
    assert metrics.total_donations == 3
    assert metrics.average_days_between_donations == 0.0


def test_repeat_donors_and_average_days_calculation(engine):
    """Computes accurate average days between consecutive donations."""
    # Donor A: Jan 1 -> March 2 (60 days) -> May 1 (60 days) -> intervals = [60, 60]
    engine.record_donation("D-A", date(2026, 1, 1))
    engine.record_donation("D-A", date(2026, 3, 2))
    engine.record_donation("D-A", date(2026, 5, 1))

    # Donor B: Feb 1 -> May 2 (90 days) -> interval = [90]
    engine.record_donation("D-B", date(2026, 2, 1))
    engine.record_donation("D-B", date(2026, 5, 2))

    # Donor C: Single-time donor
    engine.record_donation("D-C", date(2026, 4, 10))

    metrics = engine.compute_metrics()
    assert metrics.total_donors == 3
    assert metrics.repeat_donors == 2
    assert metrics.single_time_donors == 1

    # Ratio: 2 / 3 * 100 = 66.67%
    assert round(metrics.repeat_donor_ratio, 2) == 66.67
    assert round(metrics.churn_rate, 2) == 33.33

    # Intervals: [60, 60, 90] -> mean = 210 / 3 = 70.0 days
    assert metrics.average_days_between_donations == 70.0


def test_out_of_order_donation_dates(engine):
    """Correctly sorts dates entered out of chronological order."""
    engine.record_donation("D-X", date(2026, 6, 1))
    engine.record_donation("D-X", date(2026, 1, 1))
    engine.record_donation("D-X", date(2026, 3, 1))

    intervals = engine.compute_donor_intervals("D-X")
    # Jan 1 to Mar 1 = 59 days; Mar 1 to Jun 1 = 92 days
    assert intervals == [59, 92]


def test_bulk_loading_from_dicts(engine):
    """Loads records from list of dictionary objects and computes metrics."""
    records = [
        {"donor_id": "D1", "date": "2026-01-10"},
        {"donor_id": "D1", "date": "2026-03-11"},  # 60 days
        {"donor_id": "D2", "date": "2026-02-01"},
        {"donor_id": "D2", "date": "2026-04-02"},  # 60 days
    ]
    engine.load_donations(records)
    metrics = engine.compute_metrics()

    assert metrics.total_donors == 2
    assert metrics.repeat_donors == 2
    assert metrics.repeat_donor_ratio == 100.0
    assert metrics.average_days_between_donations == 60.0


def test_metrics_serialization(engine):
    """Verifies dictionary conversion from metrics dataclass."""
    engine.record_donation("D1", "2026-01-01")
    engine.record_donation("D1", "2026-04-11")  # 100 days
    metrics = engine.compute_metrics()
    d = metrics.to_dict()

    assert d["total_donors"] == 1
    assert d["repeat_donors"] == 1
    assert d["repeat_donor_ratio"] == 100.0
    assert d["average_days_between_donations"] == 100.0
    assert "D1" in d["per_donor_intervals"]
