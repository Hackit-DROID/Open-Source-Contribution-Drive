import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from line_item_auditor import (
    InvoiceLineItem,
    audit_line_item,
    audit_invoice_line_items,
    InvoiceLineItemAuditor,
)


class InvoiceLineItemAuditorTest(unittest.TestCase):
    """Test suite verifying invoice line item extension and subtotal auditor (CR-528)."""

    # -------------------------------------------------------------------
    # 1. Line Item Extension (qty * unit_price) Tests
    # -------------------------------------------------------------------

    def test_line_item_extension_calculation(self):
        """Verify calculated total equals quantity * unit_price."""
        item = InvoiceLineItem(
            description="Widget A",
            quantity=5.0,
            unit_price=12.50,
        )
        self.assertEqual(item.calculated_total, 62.50)
        audit = item.audit()
        self.assertTrue(audit["is_valid"])
        self.assertEqual(audit["calculated_total"], 62.50)

    def test_line_item_stated_total_matches(self):
        """Verify line item with matching stated total passes audit."""
        item = {
            "description": "Server Hosting",
            "quantity": 2,
            "unit_price": 50.00,
            "total": 100.00,
        }
        res = audit_line_item(item)
        self.assertTrue(res["is_valid"])
        self.assertEqual(res["status"], "VERIFIED")
        self.assertAlmostEqual(res["discrepancy"], 0.0, places=4)

    def test_line_item_stated_total_mismatch_flagged(self):
        """Verify line item with inconsistent stated total is flagged."""
        item = {
            "description": "Consulting Hours",
            "quantity": 10,
            "unit_price": 100.00,
            "total": 950.00,  # Expected 1000.00
        }
        res = audit_line_item(item)
        self.assertFalse(res["is_valid"])
        self.assertEqual(res["status"], "DISCREPANCY")
        self.assertAlmostEqual(res["discrepancy"], 50.00, places=2)

    # -------------------------------------------------------------------
    # 2. Multi-Item Subtotal Consistency & Tolerance Tests
    # -------------------------------------------------------------------

    def test_invoice_subtotal_exact_match(self):
        """Verify sum(line_totals) == invoice_subtotal matches cleanly."""
        lines = [
            {"description": "Item 1", "quantity": 2, "unit_price": 25.00},  # 50.00
            {"description": "Item 2", "quantity": 4, "unit_price": 12.50},  # 50.00
            {"description": "Item 3", "quantity": 1, "unit_price": 75.00},  # 75.00
        ]
        subtotal = 175.00
        result = audit_invoice_line_items(lines, invoice_subtotal=subtotal)

        self.assertTrue(result["is_valid"])
        self.assertTrue(result["is_subtotal_valid"])
        self.assertEqual(result["calculated_subtotal"], 175.00)
        self.assertEqual(result["discrepancy"], 0.0)
        self.assertEqual(result["status"], "VERIFIED")
        self.assertEqual(len(result["flagged_discrepancies"]), 0)

    def test_invoice_subtotal_within_rounding_tolerance(self):
        """Verify discrepancy <= 0.01 passes within rounding tolerance."""
        lines = [
            {"description": "Item A", "quantity": 3, "unit_price": 33.33},  # 99.99
        ]
        # Extracted subtotal has 1 cent rounding difference: 100.00
        result = audit_invoice_line_items(lines, invoice_subtotal=100.00, tolerance=0.01)
        self.assertTrue(result["is_valid"])
        self.assertAlmostEqual(result["discrepancy"], 0.01, places=4)

    def test_invoice_subtotal_exceeding_tolerance_flagged(self):
        """Verify discrepancy > 0.01 is flagged as mismatch."""
        lines = [
            {"description": "Part X", "quantity": 2, "unit_price": 50.00},  # 100.00
            {"description": "Part Y", "quantity": 1, "unit_price": 40.00},  # 40.00
        ]
        # Stated subtotal is 150.00 instead of 140.00 (diff: 10.00)
        result = audit_invoice_line_items(lines, invoice_subtotal=150.00)
        self.assertFalse(result["is_valid"])
        self.assertFalse(result["is_subtotal_valid"])
        self.assertEqual(result["status"], "DISCREPANCY_FLAGGED")
        self.assertEqual(result["discrepancy"], 10.00)
        self.assertTrue(any("Subtotal mismatch" in msg for msg in result["flagged_discrepancies"]))

    def test_flagging_discrepancy_greater_than_one_cent(self):
        """Verify strict check: diff of 0.02 is flagged when tolerance is 0.01."""
        lines = [
            {"description": "Service Fee", "quantity": 1, "unit_price": 100.00},
        ]
        result = audit_invoice_line_items(lines, invoice_subtotal=100.02, tolerance=0.01)
        self.assertFalse(result["is_valid"])
        self.assertAlmostEqual(result["discrepancy"], 0.02, places=4)

    # -------------------------------------------------------------------
    # 3. Comprehensive Invoice Payload Audit via Auditor Class
    # -------------------------------------------------------------------

    def test_invoice_payload_auditor_helper(self):
        """Verify InvoiceLineItemAuditor.audit_invoice processes full invoice payloads."""
        invoice_payload = {
            "invoice_id": "INV-2026-001",
            "vendor": "Acme Corp",
            "subtotal": 250.00,
            "line_items": [
                {"description": "Keyboard", "quantity": 2, "unit_price": 50.00, "total": 100.00},
                {"description": "Monitor", "quantity": 1, "unit_price": 150.00, "total": 150.00},
            ],
        }
        res = InvoiceLineItemAuditor.audit_invoice(invoice_payload)
        self.assertTrue(res["is_line_item_valid"])
        self.assertIsNotNone(res["line_item_audit"])
        self.assertEqual(res["line_item_audit"]["calculated_subtotal"], 250.00)

    def test_invoice_payload_with_individual_line_mismatch(self):
        """Verify invoice is marked invalid if an individual line extension is wrong."""
        invoice_payload = {
            "invoice_id": "INV-2026-002",
            "subtotal": 100.00,
            "line_items": [
                {"description": "Software License", "quantity": 1, "unit_price": 100.00, "total": 80.00},
            ],
        }
        res = InvoiceLineItemAuditor.audit_invoice(invoice_payload)
        self.assertFalse(res["is_line_item_valid"])
        self.assertTrue(res["line_item_audit"]["has_line_discrepancies"])


if __name__ == "__main__":
    unittest.main()
