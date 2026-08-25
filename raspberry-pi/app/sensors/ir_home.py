"""IR home-reference sensor for the sorter carousel.

The installed module is active-high: GPIO23 reads HIGH (3.3 V) at the
mechanical 0-degree reference and LOW everywhere else.  No pull resistor is
selected here; the module's measured output and the external wiring determine
the electrical idle state.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol


class HomeSensor(Protocol):
    """Small interface used by homing policy and tests."""

    def is_home(self) -> bool:
        """Return whether the carousel is at the 0-degree reference."""


class IRHomeSensor:
    """Read an active-high IR home module through ``lgpio``."""

    def __init__(self, gpio: int = 23, chip: int = 0, home_level: int = 1) -> None:
        if gpio < 0:
            raise ValueError("gpio must be non-negative")
        if home_level not in (0, 1):
            raise ValueError("home_level must be 0 or 1")
        self.gpio = gpio
        self.chip = chip
        self.home_level = home_level
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
            lgpio.gpio_claim_input(handle, self.gpio)
        except Exception as exc:
            try:
                if lgpio is not None and handle is not None:
                    lgpio.gpiochip_close(handle)
            except Exception:
                pass
            raise RuntimeError(f"unable to claim IR home GPIO: {exc}") from exc
        self._gpio = lgpio
        self._handle = handle

    def _require_started(self):
        if self._gpio is None or self._handle is None:
            raise RuntimeError("IR home sensor is not started")
        return self._gpio, self._handle

    def read_level(self) -> int:
        gpio, handle = self._require_started()
        return int(gpio.gpio_read(handle, self.gpio))

    def is_home(self) -> bool:
        return self.read_level() == self.home_level

    def close(self) -> None:
        if self._gpio is None or self._handle is None:
            return
        gpio, handle = self._gpio, self._handle
        try:
            try:
                gpio.gpio_free(handle, self.gpio)
            except Exception:
                pass
        finally:
            gpio.gpiochip_close(handle)
            self._gpio = None
            self._handle = None


class MockHomeSensor:
    """Replay deterministic home states for simulation and unit tests."""

    def __init__(self, readings: Iterable[bool] = (False,)) -> None:
        self._readings = iter(readings)
        self.read_count = 0
        self._last = False

    def is_home(self) -> bool:
        self.read_count += 1
        try:
            self._last = bool(next(self._readings))
        except StopIteration:
            pass
        return self._last
