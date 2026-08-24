"""Debounced object-presence detection from one ultrasonic sensor."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from math import isfinite

from sensors.ultrasonic import UltrasonicSensor


@dataclass(frozen=True)
class PresenceReading:
    """One sensor poll and the debounced detector state after that poll."""

    distance_cm: float | None
    present: bool
    valid: bool
    changed: bool
    timestamp: str


class ObjectPresenceDetector:
    """Convert noisy distance readings into debounced present/clear states.

    ``present_threshold_cm`` must be measured from the installed U1 geometry;
    it is a configuration value, not a hardware assumption.
    """

    def __init__(
        self,
        sensor: UltrasonicSensor,
        present_threshold_cm: float,
        present_samples: int = 2,
        clear_samples: int = 2,
    ) -> None:
        if present_threshold_cm <= 0:
            raise ValueError("present_threshold_cm must be positive")
        if present_samples <= 0 or clear_samples <= 0:
            raise ValueError("debounce sample counts must be positive")
        self.sensor = sensor
        self.present_threshold_cm = present_threshold_cm
        self.present_samples = present_samples
        self.clear_samples = clear_samples
        self.present = False
        self._present_count = 0
        self._clear_count = 0

    def poll(self) -> PresenceReading:
        distance = self.sensor.read_distance_cm()
        valid = distance is not None and isfinite(distance) and distance > 0
        previous = self.present
        if not valid:
            self._present_count = 0
            self._clear_count = 0
        elif distance <= self.present_threshold_cm:
            self._present_count += 1
            self._clear_count = 0
            if self._present_count >= self.present_samples:
                self.present = True
        else:
            self._clear_count += 1
            self._present_count = 0
            if self._clear_count >= self.clear_samples:
                self.present = False
        return PresenceReading(
            distance_cm=distance if valid else None,
            present=self.present,
            valid=valid,
            changed=self.present != previous,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
