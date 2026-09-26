"""Unit tests for Hostel Mess Supply Reorder Point Engine & Depletion Predictor (CR-852)."""

import pytest
from mess.reorder_engine import (
    MessInventoryDepletionEngine,
    MessSupplyItem,
    ReorderAlert,
    REORDER_THRESHOLD_DAYS,
)


@pytest.fixture
def engine():
    return MessInventoryDepletionEngine(reorder_threshold_days=3.0)


def test_calculates_daily_stock_consumption_rate(engine):
    """Calculates daily stock consumption rate = daily_per_student * student_count."""
    # 0.25 kg per student * 200 students = 50.0 kg/day
    rate = engine.calculate_daily_consumption(daily_per_student=0.25, student_count=200)
    assert rate == 50.0

    # 0.05 liters per student * 80 students = 4.0 liters/day
    rate_oil = engine.calculate_daily_consumption(daily_per_student=0.05, student_count=80)
    assert rate_oil == 4.0


def test_flags_reorder_warning_when_days_left_below_three(engine):
    """Flags reorder warning when current_stock / daily_consumption < 3.0 days."""
    item = MessSupplyItem(
        item_id="RICE-01",
        name="Basmati Rice",
        unit="kg",
        current_stock=100.0,
        daily_per_student=0.25,
    )
    # student_count = 200 => daily_consumption = 50.0 kg
    # days_left = 100.0 / 50.0 = 2.0 days (< 3.0 days)
    res = engine.evaluate_item(item, student_count=200)

    assert res.daily_consumption == 50.0
    assert res.days_left == 2.0
    assert res.needs_reorder is True
    assert res.alert is not None
    assert res.alert.item_id == "RICE-01"
    assert res.alert.item_name == "Basmati Rice"
    assert res.alert.severity == "WARNING"
    assert res.alert.reorder_threshold_days == 3.0
    assert res.alert.days_left == 2.0


def test_does_not_flag_reorder_when_stock_at_or_above_three_days(engine):
    """Does not flag reorder warning when current_stock / daily_consumption >= 3.0 days."""
    item = MessSupplyItem(
        item_id="WHEAT-01",
        name="Wheat Flour",
        unit="kg",
        current_stock=300.0,
        daily_per_student=0.20,
    )
    # student_count = 250 => daily_consumption = 50.0 kg
    # days_left = 300.0 / 50.0 = 6.0 days (>= 3.0 days)
    res = engine.evaluate_item(item, student_count=250)

    assert res.daily_consumption == 50.0
    assert res.days_left == 6.0
    assert res.needs_reorder is False
    assert res.alert is None


def test_boundary_at_exactly_three_days(engine):
    """At exactly 3.0 days, safety threshold is satisfied (no alert)."""
    item = MessSupplyItem(
        item_id="DAL-01",
        name="Toor Dal",
        unit="kg",
        current_stock=60.0,
        daily_per_student=0.10,
    )
    # student_count = 200 => daily_consumption = 20.0 kg
    # days_left = 60.0 / 20.0 = 3.0 days
    res = engine.evaluate_item(item, student_count=200)

    assert res.days_left == 3.0
    assert res.needs_reorder is False
    assert res.alert is None


def test_critical_severity_when_under_one_day(engine):
    """Flags CRITICAL severity when remaining stock is less than 1.0 day."""
    item = MessSupplyItem(
        item_id="MILK-01",
        name="Fresh Milk",
        unit="liters",
        current_stock=15.0,
        daily_per_student=0.20,
    )
    # student_count = 100 => daily_consumption = 20.0 liters
    # days_left = 15.0 / 20.0 = 0.75 days (< 1.0 day)
    res = engine.evaluate_item(item, student_count=100)

    assert res.days_left == 0.75
    assert res.needs_reorder is True
    assert res.alert.severity == "CRITICAL"


def test_suggested_order_quantity_calculation(engine):
    """Calculates suggested order quantity to replenish stock to target buffer."""
    item = MessSupplyItem(
        item_id="OIL-01",
        name="Cooking Oil",
        unit="liters",
        current_stock=10.0,
        daily_per_student=0.05,
    )
    # student_count = 100 => daily_consumption = 5.0 liters
    # days_left = 10.0 / 5.0 = 2.0 days
    # target 7 days = 35.0 liters total => suggested order = 35.0 - 10.0 = 25.0 liters
    res = engine.evaluate_item(item, student_count=100, target_stock_days=7.0)

    assert res.needs_reorder is True
    assert res.alert.suggested_order_quantity == 25.0


def test_evaluate_inventory_multiple_items(engine):
    """Evaluates multiple inventory items and filters active alerts."""
    items = [
        MessSupplyItem("ITEM-1", "Sufficient Item", "kg", current_stock=500.0, daily_per_student=0.1),
        MessSupplyItem("ITEM-2", "Low Item", "kg", current_stock=20.0, daily_per_student=0.1),
        MessSupplyItem("ITEM-3", "Critical Item", "kg", current_stock=5.0, daily_per_student=0.1),
    ]
    # student_count = 100 => daily_consumption = 10.0 kg for each
    # ITEM-1: 50.0 days (OK)
    # ITEM-2: 2.0 days (WARNING)
    # ITEM-3: 0.5 days (CRITICAL)
    alerts = engine.get_reorder_alerts(items, student_count=100)

    assert len(alerts) == 2
    assert alerts[0].item_id == "ITEM-2"
    assert alerts[0].severity == "WARNING"
    assert alerts[1].item_id == "ITEM-3"
    assert alerts[1].severity == "CRITICAL"


def test_zero_students_or_zero_consumption(engine):
    """Handling of zero student headcount or zero consumption."""
    item = MessSupplyItem("SPICE-01", "Salt", "kg", current_stock=20.0, daily_per_student=0.0)
    res = engine.evaluate_item(item, student_count=150)

    assert res.daily_consumption == 0.0
    assert res.days_left == float("inf")
    assert res.needs_reorder is False
    assert res.alert is None


def test_invalid_input_validation(engine):
    """Rejects negative values for stock, student count, or consumption."""
    with pytest.raises(ValueError, match="Current stock cannot be negative"):
        MessSupplyItem("ERR-1", "Error", "kg", current_stock=-5.0, daily_per_student=0.1)

    with pytest.raises(ValueError, match="Daily consumption per student cannot be negative"):
        MessSupplyItem("ERR-2", "Error", "kg", current_stock=10.0, daily_per_student=-0.1)

    with pytest.raises(ValueError, match="student_count cannot be negative"):
        engine.calculate_daily_consumption(0.1, -10)
