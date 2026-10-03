"""Unit tests for Multi-Currency Booking Billing & Daily Exchange Rate Converter (CR-755)."""

import os
import sys
import pytest

_app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _app_root not in sys.path:
    sys.path.insert(0, _app_root)

from payment.currency_converter import (
    MultiCurrencyBillingEngine,
    CurrencyConversionResult,
    SUPPORTED_CURRENCIES,
    DEFAULT_EXCHANGE_RATES_USD_BASE,
)


@pytest.fixture
def engine():
    """Returns a MultiCurrencyBillingEngine initialized with standard rates."""
    return MultiCurrencyBillingEngine(base_currency="USD")


def test_supported_currency_symbols(engine):
    """Verifies all required currency symbols ($, €, £, ¥, ₹) are configured."""
    assert engine.get_currency_symbol("USD") == "$"
    assert engine.get_currency_symbol("EUR") == "€"
    assert engine.get_currency_symbol("GBP") == "£"
    assert engine.get_currency_symbol("JPY") == "¥"
    assert engine.get_currency_symbol("INR") == "₹"


def test_daily_exchange_rate_matrix(engine):
    """Verifies daily exchange rate matrix values for supported pairs."""
    # USD to USD is 1.0
    assert engine.get_exchange_rate("USD", "USD") == 1.0
    # USD to EUR is 0.92
    assert engine.get_exchange_rate("USD", "EUR") == 0.92
    # USD to GBP is 0.79
    assert engine.get_exchange_rate("USD", "GBP") == 0.79
    # USD to JPY is 155.0
    assert engine.get_exchange_rate("USD", "JPY") == 155.0
    # USD to INR is 83.5
    assert engine.get_exchange_rate("USD", "INR") == 83.5


def test_cross_currency_exchange_rates(engine):
    """Computes cross currency exchange rates through the base currency."""
    # EUR to USD = 1.0 / 0.92 = ~1.087
    eur_to_usd = engine.get_exchange_rate("EUR", "USD")
    assert round(eur_to_usd, 4) == round(1.0 / 0.92, 4)

    # EUR to INR = 83.5 / 0.92 = ~90.7609
    eur_to_inr = engine.get_exchange_rate("EUR", "INR")
    assert round(eur_to_inr, 2) == round(83.5 / 0.92, 2)


def test_convert_billing_usd_to_eur(engine):
    """Verifies subtotal, tax, and total conversion from USD to EUR."""
    # Subtotal: $200.00, Tax (10%): $20.00, Total: $220.00
    # EUR rate = 0.92 -> Subtotal: €184.00, Tax: €18.40, Total: €202.40
    result = engine.convert_billing(subtotal=200.0, tax_rate=0.10, target_currency="EUR")

    assert result.base_currency == "USD"
    assert result.target_currency == "EUR"
    assert result.exchange_rate == 0.92
    assert result.base_subtotal == 200.0
    assert result.base_tax == 20.0
    assert result.base_total == 220.0
    assert result.converted_subtotal == 184.0
    assert result.converted_tax == 18.4
    assert result.converted_total == 202.4
    assert result.currency_symbol == "€"
    assert result.formatted_subtotal == "€184.00"
    assert result.formatted_tax == "€18.40"
    assert result.formatted_total == "€202.40"


def test_convert_billing_usd_to_inr(engine):
    """Verifies currency conversion from USD to INR with ₹ symbol."""
    # Subtotal: $100.00, Tax (15%): $15.00, Total: $115.00
    # INR rate = 83.5 -> Subtotal: ₹8350.00, Tax: ₹1252.50, Total: ₹9602.50
    result = engine.convert_billing(subtotal=100.0, tax_rate=0.15, target_currency="INR")

    assert result.converted_subtotal == 8350.0
    assert result.converted_tax == 1252.50
    assert result.converted_total == 9602.50
    assert result.currency_symbol == "₹"
    assert "₹" in result.formatted_total
    assert result.formatted_total == "₹9,602.50"


def test_convert_billing_usd_to_jpy(engine):
    """Verifies Japanese Yen formatting without decimal cents."""
    # Subtotal: $50.00, Tax (8%): $4.00, Total: $54.00
    # JPY rate = 155.0 -> Subtotal: ¥7750, Tax: ¥620, Total: ¥8370
    result = engine.convert_billing(subtotal=50.0, tax_rate=0.08, target_currency="JPY")

    assert result.converted_subtotal == 7750.0
    assert result.converted_tax == 620.0
    assert result.converted_total == 8370.0
    assert result.currency_symbol == "¥"
    assert result.formatted_subtotal == "¥7,750"
    assert result.formatted_total == "¥8,370"


def test_convert_billing_usd_to_gbp(engine):
    """Verifies British Pound formatting with £ symbol."""
    result = engine.convert_billing(subtotal=150.0, tax_rate=0.20, target_currency="GBP")

    # Rate 0.79 -> Subtotal: 150 * 0.79 = 118.50, Tax: 30 * 0.79 = 23.70, Total: 180 * 0.79 = 142.20
    assert result.converted_subtotal == 118.50
    assert result.converted_tax == 23.70
    assert result.converted_total == 142.20
    assert result.currency_symbol == "£"
    assert result.formatted_total == "£142.20"


def test_guest_receipt_generation(engine):
    """Generates structured guest billing receipt dictionary."""
    receipt = engine.generate_guest_receipt(
        booking_id="BK-9821",
        guest_name="Alice Smith",
        subtotal=300.0,
        tax_rate=0.10,
        target_currency="EUR",
    )

    assert receipt["booking_id"] == "BK-9821"
    assert receipt["guest_name"] == "Alice Smith"
    breakdown = receipt["currency_breakdown"]
    assert breakdown["target_currency"] == "EUR"
    assert breakdown["converted_pricing"]["currency_symbol"] == "€"
    assert breakdown["converted_pricing"]["formatted_total"] == "€303.60"



def test_custom_exchange_rate_override(engine):
    """Allows updating daily exchange rate dynamically."""
    engine.set_exchange_rate("EUR", 0.95)
    assert engine.get_exchange_rate("USD", "EUR") == 0.95

    result = engine.convert_billing(subtotal=100.0, tax_rate=0.0, target_currency="EUR")
    assert result.converted_total == 95.0


def test_invalid_parameters_validation(engine):
    """Validates negative subtotal, negative tax, or invalid currencies."""
    with pytest.raises(ValueError, match="negative"):
        engine.convert_billing(subtotal=-100.0, target_currency="EUR")

    with pytest.raises(ValueError, match="negative"):
        engine.convert_billing(subtotal=100.0, tax_rate=-0.05, target_currency="EUR")

    with pytest.raises(ValueError, match="Unsupported"):
        engine.convert_billing(subtotal=100.0, target_currency="XYZ")
