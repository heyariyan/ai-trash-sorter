"""Ultrasonic sensor contract and deterministic mock.

The real GPIO implementation is intentionally not included until the exact
ultrasonic module and Echo voltage are confirmed. Raspberry Pi GPIO inputs
must never receive an unverified sensor output.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol


class UltrasonicSensor(Protocol):
    """Minimal distance-reading contract used by object detection."""

    def read_distance_cm(self) -> float | None:
        """Return a distance in centimetres, or None on timeout/invalid read."""


class MockUltrasonicSensor:
    """Replay fixed distances for simulation and unit tests."""

    def __init__(self, readings_cm: Iterable[float | None] = ()) -> None:
        self._readings = iter(readings_cm)
        self.read_count = 0

    def read_distance_cm(self) -> float | None:
        self.read_count += 1
        try:
            return next(self._readings)
        except StopIteration:
            return None
