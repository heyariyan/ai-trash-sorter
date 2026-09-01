"""YES/NO/PREV/NEXT feedback input policy and GPIO adapter."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from time import monotonic, sleep


@dataclass(frozen=True)
class FeedbackResult:
    correct: bool | None
    corrected_label: str | None = None
    timed_out: bool = False


class MockFeedbackPanel:
    """Replay feedback results for tests and simulation."""

    def __init__(self, results: Iterable[FeedbackResult] = ()) -> None:
        self._results = iter(results)
        self.prompts: list[str] = []

    def wait_for_feedback(
        self,
        *,
        prediction: str,
        labels: Sequence[str],
        display,
        timeout_seconds: float,
    ) -> FeedbackResult:
        self.prompts.append(prediction)
        display.show_feedback_prompt(f"{prediction} correct? YES/NO")
        try:
            return next(self._results)
        except StopIteration:
            return FeedbackResult(correct=None, timed_out=True)

    def close(self) -> None:
        return


class TouchSwitchFeedbackPanel:
    """GPIO feedback panel using four touch switches.

    Defaults match the current planning map: YES=20, NO=21, PREV=16,
    NEXT=12. The touch-module active level must be verified before physical
    use; set ``active_level`` to match the measured output.
    """

    def __init__(
        self,
        *,
        yes_gpio: int = 20,
        no_gpio: int = 21,
        prev_gpio: int = 16,
        next_gpio: int = 12,
        chip: int = 0,
        active_level: int = 1,
        poll_seconds: float = 0.03,
    ) -> None:
        pins = (yes_gpio, no_gpio, prev_gpio, next_gpio)
        if any(pin < 0 for pin in pins) or len(set(pins)) != len(pins):
            raise ValueError("feedback GPIOs must be distinct non-negative BCM numbers")
        if active_level not in (0, 1):
            raise ValueError("active_level must be 0 or 1")
        if poll_seconds <= 0:
            raise ValueError("poll_seconds must be positive")
        self.yes_gpio = yes_gpio
        self.no_gpio = no_gpio
        self.prev_gpio = prev_gpio
        self.next_gpio = next_gpio
        self.chip = chip
        self.active_level = active_level
        self.poll_seconds = poll_seconds
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
            # Use SET_PULL_DOWN if active_level is 1, so open switches stay 0
            bias = lgpio.SET_PULL_DOWN if self.active_level == 1 else lgpio.SET_PULL_UP
            for pin in (self.yes_gpio, self.no_gpio, self.prev_gpio, self.next_gpio):
                try:
                    lgpio.gpio_claim_input(handle, pin, bias)
                except Exception:
                    lgpio.gpio_claim_input(handle, pin)
        except Exception as exc:
            try:
                if lgpio is not None and handle is not None:
                    lgpio.gpiochip_close(handle)
            except Exception:
                pass
            raise RuntimeError(f"unable to claim feedback GPIOs: {exc}") from exc
        self._gpio = lgpio
        self._handle = handle

    def _require_started(self):
        if self._gpio is None or self._handle is None:
            raise RuntimeError("feedback panel is not started")
        return self._gpio, self._handle

    def _pressed(self, pin: int) -> bool:
        """Sample multiple times with short delay to filter high-frequency noise."""
        gpio, handle = self._require_started()
        val1 = int(gpio.gpio_read(handle, pin)) == self.active_level
        if not val1:
            return False
        # Verify with 2 more samples 10ms apart (30ms total stable window)
        sleep(0.01)
        val2 = int(gpio.gpio_read(handle, pin)) == self.active_level
        if not val2:
            return False
        sleep(0.01)
        val3 = int(gpio.gpio_read(handle, pin)) == self.active_level
        return val1 and val2 and val3

    def _wait_press(
        self,
        pins: Sequence[int],
        timeout_seconds: float,
        interrupt_check=None,
    ) -> int | None:
        deadline = monotonic() + timeout_seconds
        while monotonic() < deadline:
            if interrupt_check and interrupt_check():
                return None
            for pin in pins:
                if self._pressed(pin):
                    # 30ms hardware debounce to filter out momentary noise
                    sleep(0.03)
                    if self._pressed(pin):
                        while self._pressed(pin) and monotonic() < deadline:
                            sleep(self.poll_seconds)
                        return pin
            sleep(self.poll_seconds)
        return None

    def wait_for_feedback(
        self,
        *,
        prediction: str,
        labels: Sequence[str],
        display,
        timeout_seconds: float,
        interrupt_check=None,
    ) -> FeedbackResult:
        if timeout_seconds <= 0:
            return FeedbackResult(correct=None, timed_out=True)
        labels = tuple(str(label).upper() for label in labels)
        display.show_feedback_prompt(f"{prediction} correct? YES/NO")
        pressed = self._wait_press(
            (self.yes_gpio, self.no_gpio),
            timeout_seconds,
            interrupt_check=interrupt_check,
        )
        if pressed == self.yes_gpio:
            return FeedbackResult(correct=True)
        if pressed != self.no_gpio:
            return FeedbackResult(correct=None, timed_out=True)

        selected = labels.index(prediction) if prediction in labels else 0
        deadline = monotonic() + timeout_seconds
        while monotonic() < deadline:
            display.show_feedback_prompt("Select correct bin", labels[selected])
            remaining = max(0.0, deadline - monotonic())
            pressed = self._wait_press(
                (self.prev_gpio, self.next_gpio, self.yes_gpio),
                min(timeout_seconds, remaining),
                interrupt_check=interrupt_check,
            )
            if pressed == self.prev_gpio:
                selected = (selected - 1) % len(labels)
            elif pressed == self.next_gpio:
                selected = (selected + 1) % len(labels)
            elif pressed == self.yes_gpio:
                corrected = labels[selected]
                return FeedbackResult(
                    correct=corrected == prediction,
                    corrected_label=None if corrected == prediction else corrected,
                )
            else:
                break
        return FeedbackResult(correct=None, timed_out=True)

    def close(self) -> None:
        if self._gpio is None or self._handle is None:
            return
        gpio, handle = self._gpio, self._handle
        try:
            for pin in (self.yes_gpio, self.no_gpio, self.prev_gpio, self.next_gpio):
                try:
                    gpio.gpio_free(handle, pin)
                except Exception:
                    pass
        finally:
            gpio.gpiochip_close(handle)
            self._gpio = None
            self._handle = None
