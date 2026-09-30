import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from currency_tax_auditor import (
    resolve_currency_code,
    audit_tax_calculation,
    InvoiceCurrencyAndTaxAuditor,
)


class CurrencyCodeResolverAndTaxAuditorTest(unittest.TestCase):
    """Test suite verifying currency code resolution and tax multiplier audit engine (CR-810)."""

    # -------------------------------------------------------------------
    # 1. Currency Symbol Resolution Tests
    # -------------------------------------------------------------------

    def test_currency_symbol_direct_mapping(self):
        """Verify symbols $, €, £, ₹ map to USD, EUR, GBP, INR respectively."""
        self.assertEqual(resolve_currency_code("$"), "USD")
        self.assertEqual(resolve_currency_code("€"), "EUR")
        self.assertEqual(resolve_currency_code("£"), "GBP")
        self.assertEqual(resolve_currency_code("₹"), "INR")

    def test_currency_symbol_in_text_strings(self):
        """Verify extracting currency symbols from price strings."""
        self.assertEqual(resolve_currency_code("$1,250.00"), "USD")
        self.assertEqual(resolve_currency_code("Total: €49.99"), "EUR")
        self.assertEqual(resolve_currency_code("£ 105.50 Due"), "GBP")
        self.assertEqual(resolve_currency_code("₹25,000 paid"), "INR")

    def test_currency_iso_codes_direct(self):
        """Verify ISO codes (USD, EUR, GBP, INR) are properly recognized."""
        self.assertEqual(resolve_currency_code("USD 500"), "USD")
        self.assertEqual(resolve_currency_code("EUR 200"), "EUR")
        self.assertEqual(resolve_currency_code("GBP 150"), "GBP")
        self.assertEqual(resolve_currency_code("INR 1000"), "INR")

    def test_unrecognized_or_empty_currency(self):
        """Verify None is returned for missing or unsupported symbols."""
        self.assertIsNone(resolve_currency_code(""))
        self.assertIsNone(resolve_currency_code("12345"))
        self.assertIsNone(resolve_currency_code(None))

    # -------------------------------------------------------------------
    # 2. Tax Multiplier Calculation & Tolerance Tests
    # -------------------------------------------------------------------

    def test_exact_tax_calculation_verified(self):
        """Verify valid tax calculation with zero discrepancy passes."""
        # subtotal: 1000.0, rate: 0.18 (18%), tax: 180.0
        result = audit_tax_calculation(subtotal=1000.0, tax_rate=0.18, tax_amount=180.0)
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["status"], "VERIFIED")
        self.assertAlmostEqual(result["discrepancy"], 0.0, places=4)

    def test_tax_calculation_within_tolerance(self):
        """Verify discrepancy < 0.02 is accepted as valid."""
        # subtotal: 100.0, rate: 0.0825 (8.25%), exact tax: 8.25. Given: 8.26 (diff = 0.01 < 0.02)
        result = audit_tax_calculation(subtotal=100.0, tax_rate=0.0825, tax_amount=8.26)
        self.assertTrue(result["is_valid"])
        self.assertLess(result["discrepancy"], 0.02)
        self.assertEqual(result["status"], "VERIFIED")

    def test_tax_calculation_mismatch_flagged(self):
        """Verify discrepancy >= 0.02 is flagged as mismatch."""
        # subtotal: 500.0, rate: 0.10, expected: 50.0. Given: 55.0 (diff = 5.0)
        result = audit_tax_calculation(subtotal=500.0, tax_rate=0.10, tax_amount=55.0)
        self.assertFalse(result["is_valid"])
        self.assertEqual(result["status"], "MISMATCH")
        self.assertGreaterEqual(result["discrepancy"], 0.02)
        self.assertIn("mismatch", result["message"].lower())

    def test_percentage_tax_rate_normalization(self):
        """Verify tax rate passed as whole percentage (e.g. 18.0) is normalized correctly."""
        result = audit_tax_calculation(subtotal=200.0, tax_rate=18.0, tax_amount=36.0)
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["tax_rate"], 0.18)

    # -------------------------------------------------------------------
    # 3. Invoice Full Audit Pipeline Tests
    # -------------------------------------------------------------------

    def test_audit_invoice_payload(self):
        """Verify InvoiceCurrencyAndTaxAuditor.audit_invoice processes complete payload."""
        invoice = {
            "client_name": "Acme Corp",
            "invoice_amount": "₹1180.00",
            "subtotal": 1000.0,
            "tax_rate": 18.0,
            "tax_amount": 180.0,
            "currency_symbol": "₹",
        }
        audited = InvoiceCurrencyAndTaxAuditor.audit_invoice(invoice)
        self.assertEqual(audited["currency_code"], "INR")
        self.assertTrue(audited["is_tax_valid"])
        self.assertIsNotNone(audited["tax_audit"])
        self.assertEqual(audited["tax_audit"]["status"], "VERIFIED")


if __name__ == "__main__":
    unittest.main()
