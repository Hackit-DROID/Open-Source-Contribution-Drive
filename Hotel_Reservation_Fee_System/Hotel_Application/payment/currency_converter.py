"""Multi-Currency Booking Billing & Daily Exchange Rate Converter (CR-755).

Converts base room reservation charges, taxes, and totals to target foreign
currencies (EUR, GBP, JPY, INR, USD) using daily exchange rate conversion tables,
and renders formatted guest billing receipts with regional currency symbols.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, Optional


# Supported currency codes and their official display symbols
SUPPORTED_CURRENCIES: Dict[str, str] = {
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "JPY": "¥",
    "INR": "₹",
}

# Default daily exchange rates matrix relative to USD (USD = 1.0)
DEFAULT_EXCHANGE_RATES_USD_BASE: Dict[str, float] = {
    "USD": 1.0,
    "EUR": 0.92,
    "GBP": 0.79,
    "JPY": 155.0,
    "INR": 83.5,
}


@dataclass
class CurrencyConversionResult:
    """Represents the multi-currency converted billing breakdown."""
    base_currency: str
    target_currency: str
    exchange_rate: float
    base_subtotal: float
    base_tax: float
    base_total: float
    converted_subtotal: float
    converted_tax: float
    converted_total: float
    currency_symbol: str
    formatted_subtotal: str
    formatted_tax: str
    formatted_total: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "base_currency": self.base_currency,
            "target_currency": self.target_currency,
            "exchange_rate": self.exchange_rate,
            "base_pricing": {
                "subtotal": self.base_subtotal,
                "tax": self.base_tax,
                "total": self.base_total,
            },
            "converted_pricing": {
                "subtotal": self.converted_subtotal,
                "tax": self.converted_tax,
                "total": self.converted_total,
                "currency_symbol": self.currency_symbol,
                "formatted_subtotal": self.formatted_subtotal,
                "formatted_tax": self.formatted_tax,
                "formatted_total": self.formatted_total,
            },
        }


class MultiCurrencyBillingEngine:
    """Multi-currency billing and daily exchange rate converter for hotel bookings."""

    def __init__(
        self,
        base_currency: str = "USD",
        custom_rates: Optional[Dict[str, float]] = None,
    ):
        norm_base = base_currency.strip().upper()
        if norm_base not in SUPPORTED_CURRENCIES:
            raise ValueError(f"Unsupported base currency: {base_currency}")
        self.base_currency = norm_base

        self._rates: Dict[str, float] = dict(DEFAULT_EXCHANGE_RATES_USD_BASE)
        if custom_rates:
            for curr, rate in custom_rates.items():
                self.set_exchange_rate(curr, rate)

    def get_supported_currencies(self) -> Dict[str, str]:
        """Return dictionary of supported currency codes and symbols."""
        return dict(SUPPORTED_CURRENCIES)

    def get_currency_symbol(self, currency: str) -> str:
        """Return display symbol for currency code."""
        code = currency.strip().upper()
        if code not in SUPPORTED_CURRENCIES:
            raise ValueError(f"Unsupported currency: {currency}")
        return SUPPORTED_CURRENCIES[code]

    def set_exchange_rate(self, currency: str, rate_against_usd: float) -> None:
        """Update exchange rate for a currency against USD."""
        code = currency.strip().upper()
        if code not in SUPPORTED_CURRENCIES:
            raise ValueError(f"Unsupported currency: {currency}")
        if rate_against_usd <= 0:
            raise ValueError("Exchange rate must be positive.")
        self._rates[code] = float(rate_against_usd)

    def get_exchange_rate(self, from_currency: str, to_currency: str) -> float:
        """Compute direct exchange rate multiplier from one currency to another."""
        f_curr = from_currency.strip().upper()
        t_curr = to_currency.strip().upper()

        if f_curr not in self._rates or t_curr not in self._rates:
            raise ValueError(f"Both currencies must be supported: {f_curr} -> {t_curr}")

        # Conversion through USD baseline: (to_curr_usd / from_curr_usd)
        from_usd_rate = self._rates[f_curr]
        to_usd_rate = self._rates[t_curr]
        return to_usd_rate / from_usd_rate

    @staticmethod
    def _round_currency(amount: float, currency: str) -> float:
        """Round currency appropriately (0 decimals for JPY, 2 for others)."""
        dec = Decimal(str(round(amount, 4)))
        if currency == "JPY":
            rounded = dec.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
            return float(rounded)
        else:
            rounded = dec.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            return float(rounded)

    def format_amount(self, amount: float, currency: str) -> str:
        """Render amount formatted with currency symbol and appropriate decimal places."""
        code = currency.strip().upper()
        symbol = self.get_currency_symbol(code)
        rounded = self._round_currency(amount, code)
        if code == "JPY":
            return f"{symbol}{int(rounded):,}"
        return f"{symbol}{rounded:,.2f}"

    def convert_billing(
        self,
        subtotal: float,
        tax_rate: float = 0.10,
        target_currency: str = "USD",
        base_currency: Optional[str] = None,
    ) -> CurrencyConversionResult:
        """Convert booking charges and taxes to the selected target currency."""
        if subtotal < 0:
            raise ValueError("Subtotal cannot be negative.")
        if tax_rate < 0:
            raise ValueError("Tax rate cannot be negative.")

        base_curr = (base_currency or self.base_currency).strip().upper()
        target_curr = target_currency.strip().upper()

        if base_curr not in SUPPORTED_CURRENCIES:
            raise ValueError(f"Unsupported base currency: {base_curr}")
        if target_curr not in SUPPORTED_CURRENCIES:
            raise ValueError(f"Unsupported target currency: {target_curr}")

        # Compute base figures
        base_tax = subtotal * tax_rate
        base_total = subtotal + base_tax

        # Conversion multiplier
        rate = self.get_exchange_rate(base_curr, target_curr)

        # Apply multiplier
        conv_subtotal_raw = subtotal * rate
        conv_tax_raw = base_tax * rate
        conv_total_raw = base_total * rate

        conv_subtotal = self._round_currency(conv_subtotal_raw, target_curr)
        conv_tax = self._round_currency(conv_tax_raw, target_curr)
        conv_total = self._round_currency(conv_total_raw, target_curr)

        symbol = self.get_currency_symbol(target_curr)

        return CurrencyConversionResult(
            base_currency=base_curr,
            target_currency=target_curr,
            exchange_rate=round(rate, 4),
            base_subtotal=self._round_currency(subtotal, base_curr),
            base_tax=self._round_currency(base_tax, base_curr),
            base_total=self._round_currency(base_total, base_curr),
            converted_subtotal=conv_subtotal,
            converted_tax=conv_tax,
            converted_total=conv_total,
            currency_symbol=symbol,
            formatted_subtotal=self.format_amount(conv_subtotal, target_curr),
            formatted_tax=self.format_amount(conv_tax, target_curr),
            formatted_total=self.format_amount(conv_total, target_curr),
        )

    def generate_guest_receipt(
        self,
        booking_id: str,
        guest_name: str,
        subtotal: float,
        tax_rate: float = 0.10,
        target_currency: str = "USD",
    ) -> Dict[str, Any]:
        """Generate complete formatted guest billing receipt in foreign currency."""
        conversion = self.convert_billing(
            subtotal=subtotal,
            tax_rate=tax_rate,
            target_currency=target_currency,
        )
        return {
            "booking_id": booking_id,
            "guest_name": guest_name,
            "issued_at": datetime.now(timezone.utc).isoformat(),
            "currency_breakdown": conversion.to_dict(),
        }
