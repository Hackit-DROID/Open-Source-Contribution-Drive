"""Student Hostel Check-Out Clearance & Security Deposit Refund Ledger (CR-803).

Provides an automated clearance workflow for students checking out of hostels:
audits unpaid mess bills and room damage assessment fees, calculates net security
deposit refund balance = max(0, initial_deposit - (unpaid_mess_bills + room_damage_fees)),
issues clearance certificates, and updates allocation status to 'Checked Out'.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid


@dataclass
class DamageAssessment:
    """Represents a room fixture or asset damage fee."""
    damage_id: str
    description: str
    fee: float
    assessed_by: str = "Hostel Warden"

    def __post_init__(self):
        self.description = self.description.strip()
        if self.fee < 0:
            raise ValueError(f"Damage fee cannot be negative, got {self.fee}")


@dataclass
class ClearanceCertificate:
    """Clearance record issued upon checkout completion."""
    certificate_id: str
    student_name: str
    room_no: str
    initial_deposit: float
    unpaid_mess_bills: float
    room_damage_fees: float
    total_deductions: float
    net_refund: float
    has_outstanding_liability: bool
    outstanding_liability_amount: float
    status: str
    cleared_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    damage_items: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "certificate_id": self.certificate_id,
            "student_name": self.student_name,
            "room_no": self.room_no,
            "initial_deposit": self.initial_deposit,
            "unpaid_mess_bills": self.unpaid_mess_bills,
            "room_damage_fees": self.room_damage_fees,
            "total_deductions": self.total_deductions,
            "net_refund": self.net_refund,
            "has_outstanding_liability": self.has_outstanding_liability,
            "outstanding_liability_amount": self.outstanding_liability_amount,
            "status": self.status,
            "cleared_at": self.cleared_at.isoformat(),
            "damage_items": self.damage_items,
        }


class HostelCheckOutClearanceEngine:
    """Engine executing checkout audits, refund balance calculations, and status transitions."""

    @staticmethod
    def compute_net_refund(
        initial_deposit: float,
        unpaid_mess_bills: float,
        room_damage_fees: float,
    ) -> float:
        """Compute net security deposit refund balance.

        Formula: max(0.0, initial_deposit - (unpaid_mess_bills + room_damage_fees))
        """
        if initial_deposit < 0:
            raise ValueError(f"Initial deposit cannot be negative, got {initial_deposit}")
        if unpaid_mess_bills < 0:
            raise ValueError(f"Unpaid mess bills cannot be negative, got {unpaid_mess_bills}")
        if room_damage_fees < 0:
            raise ValueError(f"Room damage fees cannot be negative, got {room_damage_fees}")

        total_deductions = unpaid_mess_bills + room_damage_fees
        return max(0.0, round(float(initial_deposit - total_deductions), 2))

    def process_checkout_clearance(
        self,
        student_name: str,
        room_no: str,
        initial_deposit: float,
        unpaid_mess_bills: float = 0.0,
        damage_assessments: Optional[List[DamageAssessment]] = None,
        hostel_record: Optional[Any] = None,
    ) -> ClearanceCertificate:
        """Execute complete check-out clearance workflow.

        - Audits unpaid mess bills and room damage assessment fees.
        - Computes net security deposit refund balance.
        - Updates student hostel allocation status to 'Checked Out'.
        - Emits structured clearance certificate.
        """
        student_name = student_name.strip()
        room_no = room_no.strip()
        if not student_name:
            raise ValueError("Student name cannot be empty.")
        if not room_no:
            raise ValueError("Room number cannot be empty.")

        damages = damage_assessments or []
        total_damage_fees = round(sum(d.fee for d in damages), 2)
        total_deductions = round(unpaid_mess_bills + total_damage_fees, 2)

        net_refund = self.compute_net_refund(
            initial_deposit=initial_deposit,
            unpaid_mess_bills=unpaid_mess_bills,
            room_damage_fees=total_damage_fees,
        )

        has_liability = total_deductions > initial_deposit
        liability_amount = (
            round(total_deductions - initial_deposit, 2) if has_liability else 0.0
        )

        # Update student hostel allocation status to 'Checked Out'
        if hostel_record is not None:
            hostel_record.status = "Checked Out"
            if hasattr(hostel_record, "save") and callable(hostel_record.save):
                hostel_record.save()

        certificate = ClearanceCertificate(
            certificate_id=f"CLR-{uuid.uuid4().hex[:8].upper()}",
            student_name=student_name,
            room_no=room_no,
            initial_deposit=round(float(initial_deposit), 2),
            unpaid_mess_bills=round(float(unpaid_mess_bills), 2),
            room_damage_fees=total_damage_fees,
            total_deductions=total_deductions,
            net_refund=net_refund,
            has_outstanding_liability=has_liability,
            outstanding_liability_amount=liability_amount,
            status="Checked Out",
            damage_items=[
                {
                    "damage_id": d.damage_id,
                    "description": d.description,
                    "fee": d.fee,
                    "assessed_by": d.assessed_by,
                }
                for d in damages
            ],
        )

        return certificate
