"""Multi-Invoice Line Item Discrepancy & Net Subtotal Auditor (CR-528).

Verifies that line-item extensions (quantity * unit_price) match individual
stated line totals and aggregate to equal the extracted invoice net subtotal
within configurable rounding tolerance (default 0.01).
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union


DEFAULT_AUDIT_TOLERANCE: float = 0.01


@dataclass
class InvoiceLineItem:
    """Represents a single line item within an invoice."""
    description: str
    quantity: float
    unit_price: float
    stated_total: Optional[float] = None

    def __post_init__(self):
        self.quantity = float(self.quantity)
        self.unit_price = float(self.unit_price)
        if self.stated_total is not None:
            self.stated_total = float(self.stated_total)

    @property
    def calculated_total(self) -> float:
        """Computes quantity * unit_price."""
        return round(self.quantity * self.unit_price, 2)

    def audit(self, tolerance: float = DEFAULT_AUDIT_TOLERANCE) -> Dict[str, Any]:
        """Audits line-item extension and verifies consistency with stated total."""
        calc_total = self.calculated_total
        has_stated = self.stated_total is not None
        diff = abs(self.stated_total - calc_total) if has_stated else 0.0
        is_consistent = diff <= tolerance if has_stated else True

        return {
            "description": self.description,
            "quantity": self.quantity,
            "unit_price": round(self.unit_price, 2),
            "calculated_total": calc_total,
            "stated_total": round(self.stated_total, 2) if has_stated else None,
            "discrepancy": round(diff, 4) if has_stated else 0.0,
            "is_valid": is_consistent,
            "status": "VERIFIED" if is_consistent else "DISCREPANCY",
        }


def audit_line_item(
    item: Union[Dict[str, Any], InvoiceLineItem],
    tolerance: float = DEFAULT_AUDIT_TOLERANCE,
) -> Dict[str, Any]:
    """Audits a single line item dictionary or object."""
    if isinstance(item, InvoiceLineItem):
        return item.audit(tolerance=tolerance)

    desc = item.get("description", "Item")
    qty = float(item.get("quantity", item.get("qty", 1.0)))
    unit_price = float(item.get("unit_price", item.get("price", 0.0)))
    stated_total = item.get("total", item.get("stated_total", item.get("line_total")))
    stated_val = float(stated_total) if stated_total is not None else None

    line_obj = InvoiceLineItem(
        description=desc,
        quantity=qty,
        unit_price=unit_price,
        stated_total=stated_val,
    )
    return line_obj.audit(tolerance=tolerance)


def audit_invoice_line_items(
    line_items: List[Union[Dict[str, Any], InvoiceLineItem]],
    invoice_subtotal: Union[int, float],
    tolerance: float = DEFAULT_AUDIT_TOLERANCE,
) -> Dict[str, Any]:
    """
    Audits a list of line items against stated invoice net subtotal.

    Acceptance criteria:
    1. Computes qty * unit_price for each invoice line item.
    2. Validates sum(line_totals) == invoice_subtotal within rounding tolerance (0.01).
    3. Flags discrepancies exceeding tolerance.
    """
    extracted_subtotal_val = float(invoice_subtotal)
    audited_lines: List[Dict[str, Any]] = []
    calculated_subtotal = 0.0
    line_discrepancies_found: List[str] = []

    for idx, item in enumerate(line_items):
        line_result = audit_line_item(item, tolerance=tolerance)
        audited_lines.append(line_result)
        calculated_subtotal += line_result["calculated_total"]

        if not line_result["is_valid"]:
            line_discrepancies_found.append(
                f"Line {idx + 1} ('{line_result['description']}'): stated total "
                f"{line_result['stated_total']} != calculated {line_result['calculated_total']} "
                f"(diff: {line_result['discrepancy']:.4f})"
            )

    calculated_subtotal = round(calculated_subtotal, 2)
    subtotal_discrepancy = round(abs(calculated_subtotal - extracted_subtotal_val), 4)
    is_subtotal_valid = subtotal_discrepancy <= tolerance

    flagged_messages: List[str] = list(line_discrepancies_found)
    if not is_subtotal_valid:
        flagged_messages.append(
            f"Subtotal mismatch: sum of line items ({calculated_subtotal:.2f}) "
            f"differs from extracted subtotal ({extracted_subtotal_val:.2f}) "
            f"by {subtotal_discrepancy:.4f} (tolerance: {tolerance})."
        )

    overall_valid = is_subtotal_valid and (len(line_discrepancies_found) == 0)

    return {
        "is_valid": overall_valid,
        "is_subtotal_valid": is_subtotal_valid,
        "calculated_subtotal": calculated_subtotal,
        "extracted_subtotal": round(extracted_subtotal_val, 2),
        "discrepancy": subtotal_discrepancy,
        "tolerance": tolerance,
        "line_item_count": len(line_items),
        "line_items": audited_lines,
        "has_line_discrepancies": len(line_discrepancies_found) > 0,
        "flagged_discrepancies": flagged_messages,
        "status": "VERIFIED" if overall_valid else "DISCREPANCY_FLAGGED",
        "message": (
            f"Invoice line items verified cleanly with subtotal {calculated_subtotal:.2f}."
            if overall_valid
            else f"Audit flagged {len(flagged_messages)} discrepancy(ies)."
        ),
    }


class InvoiceLineItemAuditor:
    """Audit engine providing helper methods for invoice line item verification."""

    @classmethod
    def audit_items(
        cls,
        line_items: List[Union[Dict[str, Any], InvoiceLineItem]],
        invoice_subtotal: Union[int, float],
        tolerance: float = DEFAULT_AUDIT_TOLERANCE,
    ) -> Dict[str, Any]:
        return audit_invoice_line_items(line_items, invoice_subtotal, tolerance=tolerance)

    @classmethod
    def audit_invoice(
        cls,
        invoice_data: Dict[str, Any],
        tolerance: float = DEFAULT_AUDIT_TOLERANCE,
    ) -> Dict[str, Any]:
        """Audits an invoice payload containing 'line_items' and 'subtotal'."""
        result = dict(invoice_data)
        line_items = invoice_data.get("line_items", [])
        subtotal = invoice_data.get("subtotal")

        if subtotal is not None and isinstance(line_items, list):
            audit_res = cls.audit_items(line_items, subtotal, tolerance=tolerance)
            result["line_item_audit"] = audit_res
            result["is_line_item_valid"] = audit_res["is_valid"]
        else:
            result["line_item_audit"] = None
            result["is_line_item_valid"] = None

        return result
