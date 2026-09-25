"""Unit tests for Automated Emergency Blood Shortage Notification & Broadcast Dispatcher (CR-801)."""

from datetime import datetime, timedelta, timezone
import unittest

from donations.emergency_dispatch import (
    BroadcastDispatchPayload,
    DonorProfile,
    EmergencyBroadcastDispatcher,
)


class TestEmergencyBroadcastDispatcher(unittest.TestCase):
    """Test suite verifying critical shortage detection, 56-day donor cooldown filtering, and broadcast logs."""

    def setUp(self):
        self.dispatcher = EmergencyBroadcastDispatcher(critical_threshold=2)
        self.today = datetime(2026, 9, 25, 12, 0, 0, tzinfo=timezone.utc)

    def test_detect_critical_shortages_under_two_units(self):
        """Shortage detected when inventory units < 2."""
        self.dispatcher.set_stock("O-", 1)   # < 2 -> Critical
        self.dispatcher.set_stock("O+", 0)   # < 2 -> Critical
        self.dispatcher.set_stock("A+", 2)   # == 2 -> Safe
        self.dispatcher.set_stock("B+", 10)  # > 2 -> Safe

        shortages = self.dispatcher.detect_critical_shortages()
        self.assertEqual(set(shortages), {"O-", "O+"})
        self.assertTrue(self.dispatcher.is_critical_shortage("O-"))
        self.assertTrue(self.dispatcher.is_critical_shortage("O+"))
        self.assertFalse(self.dispatcher.is_critical_shortage("A+"))
        self.assertFalse(self.dispatcher.is_critical_shortage("B+"))

    def test_filter_eligible_donors_cooldown_period(self):
        """Only donors with last donation > 56 days ago (or never donated) are eligible."""
        # Donor 1: donated 60 days ago (> 56) -> Eligible
        d1 = DonorProfile(
            donor_id="D1",
            name="Alice Walker",
            blood_group="O-",
            contact="555-0101",
            last_donated_at=self.today - timedelta(days=60),
        )
        # Donor 2: donated 30 days ago (<= 56) -> Ineligible
        d2 = DonorProfile(
            donor_id="D2",
            name="Bob Smith",
            blood_group="O-",
            contact="555-0102",
            last_donated_at=self.today - timedelta(days=30),
        )
        # Donor 3: never donated -> Eligible
        d3 = DonorProfile(
            donor_id="D3",
            name="Charlie Brown",
            blood_group="O-",
            contact="555-0103",
            last_donated_at=None,
        )
        # Donor 4: different blood group (A+) -> Excluded by blood group filter
        d4 = DonorProfile(
            donor_id="D4",
            name="Diana Prince",
            blood_group="A+",
            contact="555-0104",
            last_donated_at=self.today - timedelta(days=90),
        )

        for d in [d1, d2, d3, d4]:
            self.dispatcher.register_donor(d)

        eligible = self.dispatcher.filter_eligible_donors("O-", as_of_date=self.today)
        eligible_ids = [d.donor_id for d in eligible]

        self.assertIn("D1", eligible_ids)
        self.assertIn("D3", eligible_ids)
        self.assertNotIn("D2", eligible_ids)
        self.assertNotIn("D4", eligible_ids)

    def test_donor_cooldown_exact_56_day_boundary(self):
        """A donor who donated exactly 56 days ago is eligible (>= 56 days elapsed)."""
        donor_56 = DonorProfile(
            donor_id="D-56",
            name="Exact Fifty-Six",
            blood_group="B+",
            last_donated_at=self.today - timedelta(days=56),
        )
        donor_55 = DonorProfile(
            donor_id="D-55",
            name="Fifty-Five Days",
            blood_group="B+",
            last_donated_at=self.today - timedelta(days=55),
        )

        self.assertTrue(donor_56.is_eligible(current_date=self.today))
        self.assertFalse(donor_55.is_eligible(current_date=self.today))

    def test_emergency_broadcast_dispatch_payload_and_audit_log(self):
        """Dispatch generates valid alert payload and records dispatch history."""
        self.dispatcher.set_stock("AB-", 1)  # Critical shortage

        d_eligible = DonorProfile(
            donor_id="D-AB",
            name="Elena Gilbert",
            blood_group="AB-",
            contact="555-9999",
            last_donated_at=self.today - timedelta(days=70),
        )
        self.dispatcher.register_donor(d_eligible)

        payload = self.dispatcher.dispatch_emergency_broadcast(
            blood_group="AB-",
            as_of_date=self.today,
        )

        self.assertEqual(payload.blood_group, "AB-")
        self.assertEqual(payload.current_units, 1)
        self.assertEqual(payload.recipient_count, 1)
        self.assertEqual(len(payload.target_donors), 1)
        self.assertEqual(payload.target_donors[0]["donor_id"], "D-AB")
        self.assertIn("Critical shortage of AB- blood (1 units remaining)", payload.message)
        self.assertEqual(payload.status, "Dispatched")

        # Verify audit log persistence
        logs = self.dispatcher.dispatch_audit_log
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].broadcast_id, payload.broadcast_id)
        self.assertEqual(logs[0].blood_group, "AB-")

    def test_payload_dictionary_serialization(self):
        """Broadcast payload converts to valid JSON-ready dictionary."""
        payload = BroadcastDispatchPayload(
            broadcast_id="BC-12345678",
            blood_group="O+",
            current_units=0,
            recipient_count=2,
            target_donors=[{"donor_id": "D1"}, {"donor_id": "D2"}],
            message="Emergency shortage alert",
            dispatched_at=self.today,
        )
        d = payload.to_dict()
        self.assertEqual(d["broadcast_id"], "BC-12345678")
        self.assertEqual(d["blood_group"], "O+")
        self.assertEqual(d["current_units"], 0)
        self.assertEqual(d["recipient_count"], 2)
        self.assertEqual(d["status"], "Dispatched")


if __name__ == "__main__":
    unittest.main()
