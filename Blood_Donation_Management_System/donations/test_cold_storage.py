"""Unit tests for Donor Cold Storage Temperature Audit Logger & Excursion Alert Engine (CR-851)."""

from datetime import datetime, timezone
import unittest

from donations.cold_storage import (
    ColdStorageAuditLogger,
    ExcursionAlertPayload,
    ExcursionType,
    SAFE_TEMP_MAX_CELSIUS,
    SAFE_TEMP_MIN_CELSIUS,
    StoredBloodUnit,
    TemperatureReading,
)


class TestColdStorageAuditLogger(unittest.TestCase):
    """Test suite verifying temperature audit logging, excursion threshold detection, and alert payloads."""

    def setUp(self):
        self.logger = ColdStorageAuditLogger()
        self.timestamp = datetime(2026, 9, 25, 8, 30, 0, tzinfo=timezone.utc)

    def test_temperature_logging_with_timestamp_and_freezer_id(self):
        """Logged reading must accurately store freezer ID, reading ID, and timestamp."""
        reading = self.logger.log_temperature(
            freezer_id="FREEZER-01",
            temperature_celsius=4.0,
            timestamp=self.timestamp,
        )
        self.assertEqual(reading.freezer_id, "FREEZER-01")
        self.assertEqual(reading.temperature_celsius, 4.0)
        self.assertEqual(reading.recorded_at, self.timestamp)
        self.assertFalse(reading.is_excursion)
        self.assertIsNone(reading.excursion_type)

        all_readings = self.logger.get_all_readings("FREEZER-01")
        self.assertEqual(len(all_readings), 1)
        self.assertEqual(all_readings[0].reading_id, reading.reading_id)

    def test_safe_operational_boundaries(self):
        """Readings between 2.0°C and 6.0°C (inclusive) are safe and do not trigger alerts."""
        safe_temps = [2.0, 3.5, 4.0, 5.2, 6.0]
        for t in safe_temps:
            r = self.logger.log_temperature("FREEZER-SAFE", t)
            self.assertFalse(r.is_excursion, f"Temp {t}°C should be safe.")
            self.assertIsNone(r.excursion_type)

        # No alerts should be triggered
        self.assertEqual(len(self.logger.alerts), 0)

    def test_flags_cold_excursion_below_two_degrees(self):
        """Reading < 2.0°C triggers a COLD_EXCURSION alert."""
        reading = self.logger.log_temperature("FREEZER-02", 1.8, timestamp=self.timestamp)
        self.assertTrue(reading.is_excursion)
        self.assertEqual(reading.excursion_type, ExcursionType.COLD_EXCURSION)

        excursions = self.logger.get_excursion_readings("FREEZER-02")
        self.assertEqual(len(excursions), 1)
        self.assertEqual(excursions[0].temperature_celsius, 1.8)

        # Alert automatically generated
        self.assertEqual(len(self.logger.alerts), 1)
        alert = self.logger.alerts[0]
        self.assertEqual(alert.freezer_id, "FREEZER-02")
        self.assertEqual(alert.excursion_type, "COLD_EXCURSION")
        self.assertEqual(alert.recorded_temperature, 1.8)

    def test_flags_heat_excursion_above_six_degrees(self):
        """Reading > 6.0°C triggers a HEAT_EXCURSION alert."""
        reading = self.logger.log_temperature("FREEZER-03", 6.5, timestamp=self.timestamp)
        self.assertTrue(reading.is_excursion)
        self.assertEqual(reading.excursion_type, ExcursionType.HEAT_EXCURSION)

        self.assertEqual(len(self.logger.alerts), 1)
        alert = self.logger.alerts[0]
        self.assertEqual(alert.freezer_id, "FREEZER-03")
        self.assertEqual(alert.excursion_type, "HEAT_EXCURSION")
        self.assertEqual(alert.recorded_temperature, 6.5)

    def test_alert_payload_includes_affected_blood_inventory_units(self):
        """Excursion alert payload must detail all units stored in the affected freezer."""
        # Register units in FREEZER-ALPHA
        u1 = StoredBloodUnit(unit_id="UNIT-001", blood_group="O+", freezer_id="FREEZER-ALPHA")
        u2 = StoredBloodUnit(unit_id="UNIT-002", blood_group="A-", freezer_id="FREEZER-ALPHA")
        # Register unit in different FREEZER-BETA
        u3 = StoredBloodUnit(unit_id="UNIT-003", blood_group="B+", freezer_id="FREEZER-BETA")

        self.logger.register_blood_unit(u1)
        self.logger.register_blood_unit(u2)
        self.logger.register_blood_unit(u3)

        # Trigger excursion in FREEZER-ALPHA (e.g. 7.2°C)
        self.logger.log_temperature("FREEZER-ALPHA", 7.2, timestamp=self.timestamp)

        alerts = self.logger.alerts
        self.assertEqual(len(alerts), 1)
        alert = alerts[0]

        # Only the 2 units in FREEZER-ALPHA should be affected
        self.assertEqual(alert.affected_units_count, 2)
        affected_unit_ids = [u["unit_id"] for u in alert.affected_blood_units]
        self.assertEqual(set(affected_unit_ids), {"UNIT-001", "UNIT-002"})
        self.assertNotIn("UNIT-003", affected_unit_ids)
        self.assertEqual(alert.severity, "CRITICAL")

        # Serialized payload validation
        payload_dict = alert.to_dict()
        self.assertEqual(payload_dict["freezer_id"], "FREEZER-ALPHA")
        self.assertEqual(payload_dict["excursion_type"], "HEAT_EXCURSION")
        self.assertEqual(payload_dict["affected_units_count"], 2)


if __name__ == "__main__":
    unittest.main()
