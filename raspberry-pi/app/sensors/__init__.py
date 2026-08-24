"""Hardware-independent sensor interfaces."""

from .ultrasonic import MockUltrasonicSensor, UltrasonicSensor

__all__ = ["MockUltrasonicSensor", "UltrasonicSensor"]
