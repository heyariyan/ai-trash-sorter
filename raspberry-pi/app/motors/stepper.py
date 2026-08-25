"""Minimal DRV8825 stepper adapter using lgpio on Raspberry Pi.

This module contains no sorting or homing policy. It is intentionally small so
the first physical test can be bounded and disabled safely.
"""

from __future__ import annotations

from collections.abc import Callable
from time import monotonic, sleep


class StepperError(RuntimeError):
    """Raised when the GPIO stepper adapter cannot be used safely."""


class LgpioStepper:
    """DRV8825 STEP/DIR/ENABLE/RESET/SLEEP adapter using BCM GPIO numbers."""

    def __init__(
        self,
        step_gpio: int = 24,
        direction_gpio: int = 25,
        enable_gpio: int = 8,
        reset_gpio: int = 7,
        sleep_gpio: int = 9,
        chip: int = 0,
        pulse_delay_seconds: float = 0.005,
    ) -> None:
        pins = (step_gpio, direction_gpio, enable_gpio, reset_gpio, sleep_gpio)
        if any(pin < 0 for pin in pins) or len(set(pins)) != len(pins):
            raise ValueError("stepper GPIOs must be distinct non-negative BCM numbers")
        if pulse_delay_seconds <= 0:
            raise ValueError("pulse_delay_seconds must be positive")
        self.step_gpio = step_gpio
        self.direction_gpio = direction_gpio
        self.enable_gpio = enable_gpio
        self.reset_gpio = reset_gpio
        self.sleep_gpio = sleep_gpio
        self.chip = chip
        self.pulse_delay_seconds = pulse_delay_seconds
        self._gpio = None
        self._handle: int | None = None

    def start(self) -> None:
        if self._handle is not None:
            return
        try:
            import lgpio

            handle = lgpio.gpiochip_open(self.chip)
            # Claim every output in a safe state: step low, driver disabled,
            # and reset/sleep asserted. No motor current is enabled here.
            for pin, level in (
                (self.step_gpio, 0),
                (self.direction_gpio, 0),
                (self.enable_gpio, 1),
                (self.reset_gpio, 0),
                (self.sleep_gpio, 0),
            ):
                lgpio.gpio_claim_output(handle, pin, level)
        except Exception as exc:
            try:
                lgpio.gpiochip_close(handle)
            except Exception:
                pass
            raise StepperError(f"unable to claim DRV8825 GPIOs: {exc}") from exc
        self._gpio = lgpio
        self._handle = handle

    def _require_started(self):
        if self._gpio is None or self._handle is None:
            raise StepperError("stepper is not started")
        return self._gpio, self._handle

    def enable(self) -> None:
        gpio, handle = self._require_started()
        # DRV8825 ENABLE is active-low.
        gpio.gpio_write(handle, self.enable_gpio, 0)

    def disable(self) -> None:
        if self._gpio is not None and self._handle is not None:
            self._gpio.gpio_write(self._handle, self.enable_gpio, 1)

    def move_steps(self, steps: int, direction: int = 0) -> None:
        gpio, handle = self._require_started()
        if steps <= 0:
            raise ValueError("steps must be positive")
        if direction not in (0, 1):
            raise ValueError("direction must be 0 or 1")
        gpio.gpio_write(handle, self.direction_gpio, direction)
        gpio.gpio_write(handle, self.reset_gpio, 1)
        gpio.gpio_write(handle, self.sleep_gpio, 1)
        sleep(0.01)
        self.enable()
        try:
            for _ in range(steps):
                gpio.gpio_write(handle, self.step_gpio, 1)
                sleep(self.pulse_delay_seconds)
                gpio.gpio_write(handle, self.step_gpio, 0)
                sleep(self.pulse_delay_seconds)
        finally:
            self.disable()

    def move_step_observed(
        self,
        direction: int,
        sample: Callable[[], bool],
        sample_interval_seconds: float = 0.001,
    ) -> bool:
        """Pulse one step while sampling a stop sensor during both phases."""

        gpio, handle = self._require_started()
        if direction not in (0, 1):
            raise ValueError("direction must be 0 or 1")
        if sample_interval_seconds <= 0:
            raise ValueError("sample_interval_seconds must be positive")
        gpio.gpio_write(handle, self.direction_gpio, direction)
        gpio.gpio_write(handle, self.reset_gpio, 1)
        gpio.gpio_write(handle, self.sleep_gpio, 1)
        sleep(0.01)
        self.enable()

        def sample_window(duration: float) -> bool:
            deadline = monotonic() + duration
            while monotonic() < deadline:
                if sample():
                    return True
                remaining = deadline - monotonic()
                if remaining > 0:
                    sleep(min(sample_interval_seconds, remaining))
            return bool(sample())

        home_seen = False
        try:
            gpio.gpio_write(handle, self.step_gpio, 1)
            home_seen = sample_window(self.pulse_delay_seconds)
            gpio.gpio_write(handle, self.step_gpio, 0)
            if not home_seen:
                home_seen = sample_window(self.pulse_delay_seconds)
            return home_seen
        finally:
            gpio.gpio_write(handle, self.step_gpio, 0)
            self.disable()

    def move_for_seconds(self, seconds: float, direction: int = 0) -> int:
        """Pulse continuously for a bounded duration and return pulse count."""
        gpio, handle = self._require_started()
        if seconds <= 0:
            raise ValueError("seconds must be positive")
        if direction not in (0, 1):
            raise ValueError("direction must be 0 or 1")
        gpio.gpio_write(handle, self.direction_gpio, direction)
        gpio.gpio_write(handle, self.reset_gpio, 1)
        gpio.gpio_write(handle, self.sleep_gpio, 1)
        sleep(0.01)
        self.enable()
        deadline = monotonic() + seconds
        pulses = 0
        try:
            while monotonic() < deadline:
                gpio.gpio_write(handle, self.step_gpio, 1)
                sleep(self.pulse_delay_seconds)
                gpio.gpio_write(handle, self.step_gpio, 0)
                sleep(self.pulse_delay_seconds)
                pulses += 1
        finally:
            self.disable()
        return pulses

    def close(self) -> None:
        if self._gpio is None or self._handle is None:
            return
        gpio, handle = self._gpio, self._handle
        try:
            self.disable()
            gpio.gpio_write(handle, self.step_gpio, 0)
            gpio.gpio_write(handle, self.reset_gpio, 0)
            gpio.gpio_write(handle, self.sleep_gpio, 0)
            for pin in (
                self.step_gpio,
                self.direction_gpio,
                self.enable_gpio,
                self.reset_gpio,
                self.sleep_gpio,
            ):
                try:
                    gpio.gpio_free(handle, pin)
                except Exception:
                    pass
        finally:
            gpio.gpiochip_close(handle)
            self._gpio = None
            self._handle = None
