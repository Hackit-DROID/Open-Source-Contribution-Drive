"""Unit tests for Emergency Blood Request Priority Escalation Workflow (CR-751)."""

import unittest
from datetime import datetime, timedelta, timezone

from donations.priority_escalation import (
    BloodRequestItem,
    EmergencyPriorityQueue,
    UrgencyLevel,
    get_urgency_weight,
    normalize_urgency_level,
)


class TestPriorityEscalationWorkflow(unittest.TestCase):
    """Test suite verifying request priority sorting, promotion, and compatibility matching."""

    def setUp(self):
        self.queue = EmergencyPriorityQueue()
        self.base_time = datetime(2026, 9, 25, 10, 0, 0, tzinfo=timezone.utc)

    def test_urgency_level_normalization_and_weights(self):
        """Ensure urgency levels normalize accurately and map to correct numeric weights."""
        self.assertEqual(normalize_urgency_level("Routine"), UrgencyLevel.ROUTINE.value)
        self.assertEqual(normalize_urgency_level("urgent"), UrgencyLevel.URGENT.value)
        self.assertEqual(normalize_urgency_level("Emergency ICU"), UrgencyLevel.EMERGENCY_ICU.value)
        self.assertEqual(normalize_urgency_level("icu"), UrgencyLevel.EMERGENCY_ICU.value)
        self.assertEqual(normalize_urgency_level("unknown"), UrgencyLevel.ROUTINE.value)

        self.assertEqual(get_urgency_weight("Emergency ICU"), 100)
        self.assertEqual(get_urgency_weight("Urgent"), 50)
        self.assertEqual(get_urgency_weight("Routine"), 10)
        self.assertTrue(get_urgency_weight("Emergency ICU") > get_urgency_weight("Urgent") > get_urgency_weight("Routine"))

    def test_queue_ordering_promotes_emergency_icu_ahead_of_routine(self):
        """Emergency ICU requests must automatically appear ahead of Routine requests."""
        # Create requests at different times
        req_routine = BloodRequestItem(
            request_id="REQ-001",
            patient_name="Alice",
            blood_group="A+",
            units=2,
            hospital="General Hospital",
            urgency_level="Routine",
            created_at=self.base_time,
        )
        req_emergency = BloodRequestItem(
            request_id="REQ-002",
            patient_name="Bob",
            blood_group="O+",
            units=4,
            hospital="Trauma Center",
            urgency_level="Emergency ICU",
            created_at=self.base_time + timedelta(minutes=15),  # Arrived later
        )
        req_urgent = BloodRequestItem(
            request_id="REQ-003",
            patient_name="Charlie",
            blood_group="B+",
            units=1,
            hospital="City Hospital",
            urgency_level="Urgent",
            created_at=self.base_time + timedelta(minutes=5),
        )

        # Add in non-sorted order
        self.queue.add_request(req_routine)
        self.queue.add_request(req_emergency)
        self.queue.add_request(req_urgent)

        prioritized = self.queue.get_prioritized_queue()
        ids = [item.request_id for item in prioritized]

        # Emergency ICU (REQ-002) must be first, then Urgent (REQ-003), then Routine (REQ-001)
        self.assertEqual(ids, ["REQ-002", "REQ-003", "REQ-001"])

    def test_queue_fifo_within_same_urgency_level(self):
        """Requests with identical urgency level must maintain FIFO creation order."""
        req1 = BloodRequestItem(
            request_id="ICU-1",
            patient_name="Dave",
            blood_group="AB+",
            units=2,
            hospital="Hospital A",
            urgency_level="Emergency ICU",
            created_at=self.base_time,
        )
        req2 = BloodRequestItem(
            request_id="ICU-2",
            patient_name="Eve",
            blood_group="O-",
            units=3,
            hospital="Hospital B",
            urgency_level="Emergency ICU",
            created_at=self.base_time + timedelta(minutes=10),
        )

        self.queue.add_request(req2)
        self.queue.add_request(req1)

        prioritized = self.queue.get_prioritized_queue()
        self.assertEqual([item.request_id for item in prioritized], ["ICU-1", "ICU-2"])

    def test_dynamic_promotion_to_emergency(self):
        """Promoting a routine request dynamically moves it to the top of the queue."""
        req_routine = BloodRequestItem(
            request_id="REQ-101",
            patient_name="Frank",
            blood_group="A-",
            units=1,
            hospital="Metro Clinic",
            urgency_level="Routine",
            created_at=self.base_time,
        )
        req_urgent = BloodRequestItem(
            request_id="REQ-102",
            patient_name="Grace",
            blood_group="A-",
            units=2,
            hospital="Metro Clinic",
            urgency_level="Urgent",
            created_at=self.base_time + timedelta(minutes=5),
        )

        self.queue.add_request(req_routine)
        self.queue.add_request(req_urgent)

        # Before escalation: Urgent > Routine
        self.assertEqual([i.request_id for i in self.queue.get_prioritized_queue()], ["REQ-102", "REQ-101"])

        # Escalate REQ-101 to Emergency ICU
        promoted = self.queue.promote_to_emergency("REQ-101", reason="Acute internal hemorrhage")
        self.assertEqual(promoted.urgency_level, "Emergency ICU")
        self.assertTrue(promoted.is_emergency)

        # After escalation: REQ-101 is now first
        self.assertEqual([i.request_id for i in self.queue.get_prioritized_queue()], ["REQ-101", "REQ-102"])

    def test_match_compatible_inventory_units(self):
        """Emergency request should match all compatible blood units from inventory."""
        req = BloodRequestItem(
            request_id="REQ-201",
            patient_name="Helen",
            blood_group="A+",
            units=2,
            hospital="Surgical Center",
            urgency_level="Emergency ICU",
        )
        self.queue.add_request(req)

        # Inventory units: A+ can receive O-, O+, A-, A+
        inventory = [
            {"unit_id": "U1", "blood_group": "O-", "status": "Available"},
            {"unit_id": "U2", "blood_group": "A+", "status": "Available"},
            {"unit_id": "U3", "blood_group": "B+", "status": "Available"},      # Incompatible
            {"unit_id": "U4", "blood_group": "AB+", "status": "Available"},     # Incompatible
            {"unit_id": "U5", "blood_group": "O+", "status": "Reserved"},       # Not available
        ]

        matched = self.queue.match_compatible_inventory("REQ-201", inventory)
        matched_ids = [u["unit_id"] for u in matched]
        self.assertEqual(matched_ids, ["U1", "U2"])

    def test_audit_logging_of_escalation_events(self):
        """Escalation operations must be recorded in the audit log."""
        req = BloodRequestItem(
            request_id="REQ-301",
            patient_name="Ian",
            blood_group="B-",
            units=2,
            hospital="Central Ward",
            urgency_level="Routine",
        )
        self.queue.add_request(req)
        self.queue.promote_to_emergency("REQ-301", reason="Vascular trauma")

        logs = self.queue.audit_log
        self.assertEqual(len(logs), 2)
        self.assertEqual(logs[0]["event_type"], "REQUEST_ADDED")
        self.assertEqual(logs[1]["event_type"], "PRIORITY_ESCALATED")
        self.assertEqual(logs[1]["details"]["reason"], "Vascular trauma")


if __name__ == "__main__":
    unittest.main()
