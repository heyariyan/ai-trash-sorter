"""MG995 servo and drop-gate abstractions.

    The GPIO implementation emits standard 50 Hz servo pulses on BCM GPIO18.
    The installed gate is reversed: 0 degrees maps to 2500 us and 90 degrees
    maps to 1500 us. Pulse limits and angles remain configurable.
"""

from __future__ import annotations

from dataclasses import dataclass
from time import sleep


class ServoError(RuntimeError):
    """Raised when the servo cannot be started or safely controlled."""


class LgpioServo:
    """Hardware-separated MG995 PWM adapter using ``lgpio``."""

    def __init__(
        self,
        signal_gpio: int = 18,
        chip: int = 0,
        frequency_hz: int = 50,
        min_pulse_us: int = 500,
        max_pulse_us: int = 2500,
        reverse: bool = True,
    ) -> None:
        if signal_gpio < 0:
            raise ValueError("signal_gpio must be non-negative")
        if frequency_hz <= 0:
            raise ValueError("frequency_hz must be positive")
        if min_pulse_us <= 0 or max_pulse_us <= min_pulse_us:
            raise ValueError("invalid servo pulse limits")
        self.signal_gpio = signal_gpio
        self.chip = chip
        self.frequency_hz = frequency_hz
        self.min_pulse_us = min_pulse_us
        self.max_pulse_us = max_pulse_us
        self.reverse = reverse
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
            # Claim low and do not start PWM until an explicit angle command.
            lgpio.gpio_claim_output(handle, self.signal_gpio, 0)
        except Exception as exc:
            try:
                if lgpio is not None and handle is not None:
                    lgpio.gpiochip_close(handle)
            except Exception:
                pass
            raise ServoError(f"unable to claim servo GPIO: {exc}") from exc
        self._gpio = lgpio
        self._handle = handle

    def _require_started(self):
        if self._gpio is None or self._handle is None:
            raise ServoError("servo is not started")
        return self._gpio, self._handle

    def set_pulse_us(self, pulse_us: int) -> None:
        gpio, handle = self._require_started()
        if not self.min_pulse_us <= pulse_us <= self.max_pulse_us:
            raise ValueError(
                f"pulse_us must be between {self.min_pulse_us} and {self.max_pulse_us}"
            )
        gpio.tx_servo(handle, self.signal_gpio, pulse_us, self.frequency_hz)

    def pulse_for_angle(self, angle: float) -> int:
        if not 0 <= angle <= 180:
            raise ValueError("angle must be between 0 and 180 degrees")
        fraction = angle / 180
        if self.reverse:
            fraction = 1 - fraction
        return round(
            self.min_pulse_us + (self.max_pulse_us - self.min_pulse_us) * fraction
        )

    def set_angle(self, angle: float) -> None:
        self.set_pulse_us(self.pulse_for_angle(angle))

    def stop(self) -> None:
        if self._gpio is None or self._handle is None:
            return
        gpio, handle = self._gpio, self._handle
        try:
            try:
                gpio.tx_servo(handle, self.signal_gpio, 0, 0)
            except Exception:
                pass
            try:
                gpio.gpio_free(handle, self.signal_gpio)
            except Exception:
                pass
        finally:
            gpio.gpiochip_close(handle)
            self._gpio = None
            self._handle = None


class MockServo:
    """Deterministic servo substitute for simulation and unit tests."""

    def __init__(self) -> None:
        self.started = False
        self.positions: list[float] = []

    def start(self) -> None:
        self.started = True

    def set_angle(self, angle: float) -> None:
        if not self.started:
            raise ServoError("mock servo is not started")
        self.positions.append(angle)

    def stop(self) -> None:
        self.started = False


@dataclass(frozen=True)
class GateConfig:
    closed_angle: float = 0.0
    open_angle: float = 90.0
    settle_seconds: float = 0.5

    def __post_init__(self) -> None:
        for name, angle in (("closed_angle", self.closed_angle), ("open_angle", self.open_angle)):
            if not 0 <= angle <= 180:
                raise ValueError(f"{name} must be between 0 and 180")
        if self.settle_seconds < 0:
            raise ValueError("settle_seconds cannot be negative")


class ServoGate:
    """Open/close policy independent of PWM/GPIO details."""

    def __init__(self, servo, config: GateConfig | None = None) -> None:
        self.servo = servo
        self.config = config or GateConfig()
        self.is_open = False

    def close(self) -> None:
        self.servo.set_angle(self.config.closed_angle)
        sleep(self.config.settle_seconds)
        self.is_open = False

    def open(self) -> None:
        self.servo.set_angle(self.config.open_angle)
        sleep(self.config.settle_seconds)
        self.is_open = True
