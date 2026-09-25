"""Donor Cold Storage Temperature Audit Logger & Excursion Alert Engine (CR-851).

Maintains continuous temperature audit logging for blood bank cold storage units,
flags thermal excursion events breaching safe thresholds (2.0°C–6.0°C),
and generates emergency alert payloads detailing affected blood inventory units.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid


class ExcursionType(str, Enum):
    """Classification of thermal excursion events."""
    COLD_EXCURSION = "COLD_EXCURSION"  # Temperature < 2.0°C
    HEAT_EXCURSION = "HEAT_EXCURSION"  # Temperature > 6.0°C


SAFE_TEMP_MIN_CELSIUS: float = 2.0
SAFE_TEMP_MAX_CELSIUS: float = 6.0


@dataclass
class TemperatureReading:
    """Audit log entry capturing cold storage temperature at a given point in time."""
    reading_id: str
    freezer_id: str
    temperature_celsius: float
    recorded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_excursion(self) -> bool:
        """True if temperature breaches the safe range [2.0°C, 6.0°C]."""
        return self.temperature_celsius < SAFE_TEMP_MIN_CELSIUS or self.temperature_celsius > SAFE_TEMP_MAX_CELSIUS

    @property
    def excursion_type(self) -> Optional[ExcursionType]:
        """Classify direction of excursion, or None if reading is within safe bounds."""
        if self.temperature_celsius < SAFE_TEMP_MIN_CELSIUS:
            return ExcursionType.COLD_EXCURSION
        if self.temperature_celsius > SAFE_TEMP_MAX_CELSIUS:
            return ExcursionType.HEAT_EXCURSION
        return None


@dataclass
class StoredBloodUnit:
    """Represents a blood inventory unit housed within a specific cold storage freezer."""
    unit_id: str
    blood_group: str
    freezer_id: str
    volume_ml: int = 450
    status: str = "Active"

    def __post_init__(self):
        self.blood_group = self.blood_group.strip().upper()


@dataclass
class ExcursionAlertPayload:
    """Structured alert generated when cold storage breaches safe temperature bounds."""
    alert_id: str
    freezer_id: str
    recorded_temperature: float
    excursion_type: str
    timestamp: datetime
    affected_units_count: int
    affected_blood_units: List[Dict[str, Any]]
    severity: str = "CRITICAL"
    recommended_action: str = "Quarantine affected units immediately for medical quality inspection"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "freezer_id": self.freezer_id,
            "recorded_temperature": self.recorded_temperature,
            "excursion_type": self.excursion_type,
            "timestamp": self.timestamp.isoformat(),
            "affected_units_count": self.affected_units_count,
            "affected_blood_units": self.affected_blood_units,
            "severity": self.severity,
            "recommended_action": self.recommended_action,
        }


class ColdStorageAuditLogger:
    """Manages cold storage temperature audit logs, excursion detection, and alert payloads."""

    def __init__(self):
        self._readings: List[TemperatureReading] = []
        self._units: Dict[str, StoredBloodUnit] = {}
        self._alert_history: List[ExcursionAlertPayload] = []

    def register_blood_unit(self, unit: StoredBloodUnit) -> None:
        """Register a blood inventory unit inside a storage freezer."""
        self._units[unit.unit_id] = unit

    def get_units_in_freezer(self, freezer_id: str) -> List[StoredBloodUnit]:
        """Fetch all blood units currently housed in a designated freezer."""
        return [unit for unit in self._units.values() if unit.freezer_id == freezer_id]

    def log_temperature(
        self,
        freezer_id: str,
        temperature_celsius: float,
        timestamp: Optional[datetime] = None
    ) -> TemperatureReading:
        """Record a temperature audit reading and automatically trigger excursion alerts if breached."""
        reading = TemperatureReading(
            reading_id=f"TMP-{uuid.uuid4().hex[:8].upper()}",
            freezer_id=freezer_id,
            temperature_celsius=float(temperature_celsius),
            recorded_at=timestamp or datetime.now(timezone.utc),
        )
        self._readings.append(reading)

        # Trigger excursion alert when safe bounds [2.0°C, 6.0°C] are breached
        if reading.is_excursion:
            self._create_excursion_alert(reading)

        return reading

    def _create_excursion_alert(self, reading: TemperatureReading) -> ExcursionAlertPayload:
        """Construct alert payload for affected inventory units in the compromised freezer."""
        compromised_units = self.get_units_in_freezer(reading.freezer_id)
        affected_summary = [
            {
                "unit_id": u.unit_id,
                "blood_group": u.blood_group,
                "freezer_id": u.freezer_id,
                "volume_ml": u.volume_ml,
                "status": u.status,
            }
            for u in compromised_units
        ]

        excursion_name = reading.excursion_type.value if reading.excursion_type else "UNKNOWN"
        alert = ExcursionAlertPayload(
            alert_id=f"EXC-{uuid.uuid4().hex[:8].upper()}",
            freezer_id=reading.freezer_id,
            recorded_temperature=reading.temperature_celsius,
            excursion_type=excursion_name,
            timestamp=reading.recorded_at,
            affected_units_count=len(affected_summary),
            affected_blood_units=affected_summary,
            severity="CRITICAL",
        )
        self._alert_history.append(alert)
        return alert

    def get_all_readings(self, freezer_id: Optional[str] = None) -> List[TemperatureReading]:
        """Retrieve recorded temperature readings, optionally filtered by freezer ID."""
        if freezer_id:
            return [r for r in self._readings if r.freezer_id == freezer_id]
        return list(self._readings)

    def get_excursion_readings(self, freezer_id: Optional[str] = None) -> List[TemperatureReading]:
        """Retrieve only readings that breached safe operational boundaries."""
        readings = self.get_all_readings(freezer_id=freezer_id)
        return [r for r in readings if r.is_excursion]

    @property
    def alerts(self) -> List[ExcursionAlertPayload]:
        """Return history of all generated thermal excursion alerts."""
        return list(self._alert_history)
