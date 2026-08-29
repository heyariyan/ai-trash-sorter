"""Ultrasonic sensor contract, GPIO adapter, and deterministic mock.

The GPIO adapter assumes the Echo signal presented to the Pi is already safe
for a 3.3 V input. HC-SR04-style 5 V Echo pins must use a verified divider or
level shifter before this code is run against real hardware.
"""

from __future__ import annotations

from collections.abc import Iterable
from time import monotonic, sleep
from typing import Protocol


class UltrasonicSensor(Protocol):
    """Minimal distance-reading contract used by object detection."""

    def read_distance_cm(self) -> float | None:
        """Return a distance in centimetres, or None on timeout/invalid read."""


class LgpioUltrasonicSensor:
    """HC-SR04-style ultrasonic distance sensor using BCM GPIO numbers."""

    def __init__(
        self,
        trigger_gpio: int,
        echo_gpio: int,
        *,
        chip: int = 0,
        timeout_seconds: float = 0.03,
        trigger_pulse_seconds: float = 0.00001,
        speed_of_sound_cm_s: float = 34300.0,
    ) -> None:
        if trigger_gpio < 0 or echo_gpio < 0 or trigger_gpio == echo_gpio:
            raise ValueError("trigger and echo GPIOs must be distinct non-negative BCM numbers")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if trigger_pulse_seconds <= 0:
            raise ValueError("trigger_pulse_seconds must be positive")
        if speed_of_sound_cm_s <= 0:
            raise ValueError("speed_of_sound_cm_s must be positive")
        self.trigger_gpio = trigger_gpio
        self.echo_gpio = echo_gpio
        self.chip = chip
        self.timeout_seconds = timeout_seconds
        self.trigger_pulse_seconds = trigger_pulse_seconds
        self.speed_of_sound_cm_s = speed_of_sound_cm_s
        self._gpio = None
        self._handle: int | None = None

    def start(self) -> None:
        if self._handle is not None:
            return
        lgpio = None
        handle = None
        try:
            import lgpio

            handle = lgpio.gpiochip_open(self.chip)
            lgpio.gpio_claim_output(handle, self.trigger_gpio, 0)
            lgpio.gpio_claim_input(handle, self.echo_gpio)
        except Exception as exc:
            try:
                if lgpio is not None and handle is not None:
                    lgpio.gpiochip_close(handle)
            except Exception:
                pass
            raise RuntimeError(f"unable to claim ultrasonic GPIOs: {exc}") from exc
        self._gpio = lgpio
        self._handle = handle

    def _require_started(self):
        if self._gpio is None or self._handle is None:
            raise RuntimeError("ultrasonic sensor is not started")
        return self._gpio, self._handle

    def read_distance_cm(self) -> float | None:
        gpio, handle = self._require_started()
        gpio.gpio_write(handle, self.trigger_gpio, 0)
        sleep(0.000002)
        gpio.gpio_write(handle, self.trigger_gpio, 1)
        sleep(self.trigger_pulse_seconds)
        gpio.gpio_write(handle, self.trigger_gpio, 0)

        deadline = monotonic() + self.timeout_seconds
        while gpio.gpio_read(handle, self.echo_gpio) == 0:
            if monotonic() >= deadline:
                return None

        echo_started = monotonic()
        deadline = echo_started + self.timeout_seconds
        while gpio.gpio_read(handle, self.echo_gpio) == 1:
            if monotonic() >= deadline:
                return None

        duration = monotonic() - echo_started
        return round((duration * self.speed_of_sound_cm_s) / 2, 3)

    def close(self) -> None:
        if self._gpio is None or self._handle is None:
            return
        gpio, handle = self._gpio, self._handle
        try:
            try:
                gpio.gpio_write(handle, self.trigger_gpio, 0)
            except Exception:
                pass
            for pin in (self.trigger_gpio, self.echo_gpio):
                try:
                    gpio.gpio_free(handle, pin)
                except Exception:
                    pass
        finally:
            gpio.gpiochip_close(handle)
            self._gpio = None
            self._handle = None


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
