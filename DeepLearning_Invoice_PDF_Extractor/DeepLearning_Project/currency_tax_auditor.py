import re
from typing import Any, Dict, Optional, Tuple, Union

# ---------------------------------------------------------------------------
# Currency Symbol to ISO Code Mapping
# ---------------------------------------------------------------------------

CURRENCY_SYMBOL_MAP: Dict[str, str] = {
    "$": "USD",
    "€": "EUR",
    "£": "GBP",
    "₹": "INR",
}

# Regex to detect currency symbol or standard ISO code
CURRENCY_REGEX = re.compile(r"([$€£₹])|(USD|EUR|GBP|INR)", re.IGNORECASE)


def resolve_currency_code(text_or_symbol: str) -> Optional[str]:
    """
    Identifies currency symbol ($, €, £, ₹) or code in a string
    and maps it to standard ISO currency code (USD, EUR, GBP, INR).
    """
    if not text_or_symbol or not isinstance(text_or_symbol, str):
        return None

    # Direct match in map
    cleaned = text_or_symbol.strip()
    if cleaned in CURRENCY_SYMBOL_MAP:
        return CURRENCY_SYMBOL_MAP[cleaned]

    # Search for symbol or ISO code
    match = CURRENCY_REGEX.search(cleaned)
    if match:
        symbol, code = match.groups()
        if symbol:
            return CURRENCY_SYMBOL_MAP.get(symbol)
        if code:
            return code.upper()

    return None


# ---------------------------------------------------------------------------
# Tax Multiplier Auditor
# ---------------------------------------------------------------------------

def audit_tax_calculation(
    subtotal: Union[int, float],
    tax_rate: Union[int, float],
    tax_amount: Union[int, float],
    tolerance: float = 0.02
) -> Dict[str, Any]:
    """
    Verifies tax calculation math: abs(tax_amount - (subtotal * normalized_tax_rate)) < 0.02.
    Accepts tax_rate as either decimal ratio (e.g. 0.18) or percentage (e.g. 18.0).
    """
    subtotal_val = float(subtotal)
    tax_amount_val = float(tax_amount)
    raw_rate = float(tax_rate)

    # Normalize percentage rate (e.g. 18% -> 0.18) if given as > 1.0
    normalized_rate = raw_rate / 100.0 if raw_rate > 1.0 else raw_rate

    expected_tax = subtotal_val * normalized_rate
    discrepancy = abs(tax_amount_val - expected_tax)
    is_valid = discrepancy < tolerance

    return {
        "is_valid": is_valid,
        "subtotal": round(subtotal_val, 2),
        "tax_rate": round(normalized_rate, 4),
        "tax_amount": round(tax_amount_val, 2),
        "expected_tax": round(expected_tax, 2),
        "discrepancy": round(discrepancy, 4),
        "tolerance": tolerance,
        "status": "VERIFIED" if is_valid else "MISMATCH",
        "message": (
            f"Tax calculation verified within {tolerance} tolerance."
            if is_valid
            else f"Tax calculation mismatch: expected {expected_tax:.2f}, got {tax_amount_val:.2f} (diff: {discrepancy:.4f})."
        ),
    }


# ---------------------------------------------------------------------------
# Invoice Currency & Tax Auditor Engine
# ---------------------------------------------------------------------------

class InvoiceCurrencyAndTaxAuditor:
    """Audit engine resolving currency symbols and auditing invoice tax math."""

    @classmethod
    def resolve_currency(cls, text: str) -> Optional[str]:
        return resolve_currency_code(text)

    @classmethod
    def verify_tax(
        cls,
        subtotal: Union[int, float],
        tax_rate: Union[int, float],
        tax_amount: Union[int, float],
        tolerance: float = 0.02
    ) -> Dict[str, Any]:
        return audit_tax_calculation(subtotal, tax_rate, tax_amount, tolerance)

    @classmethod
    def audit_invoice(cls, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Audits an invoice payload dictionary:
        Resolves currency code from text/fields and validates tax multiplier math.
        """
        result = dict(invoice_data)

        # Resolve currency from potential keys
        raw_currency = (
            invoice_data.get("currency")
            or invoice_data.get("currency_symbol")
            or invoice_data.get("raw_text", "")
            or str(invoice_data.get("invoice_amount", ""))
        )
        result["currency_code"] = cls.resolve_currency(str(raw_currency))

        # Audit tax if subtotal, tax_rate, and tax_amount exist
        subtotal = invoice_data.get("subtotal")
        tax_rate = invoice_data.get("tax_rate")
        tax_amount = invoice_data.get("tax_amount")

        if subtotal is not None and tax_rate is not None and tax_amount is not None:
            tax_audit = cls.verify_tax(subtotal, tax_rate, tax_amount)
            result["tax_audit"] = tax_audit
            result["is_tax_valid"] = tax_audit["is_valid"]
        else:
            result["tax_audit"] = None
            result["is_tax_valid"] = None

        return result
