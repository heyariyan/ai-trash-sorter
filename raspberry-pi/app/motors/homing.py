"""Bounded, sensor-checked stepper homing policy.

This module contains no GPIO code.  It coordinates a stepper adapter and a
home sensor so it can be exercised without hardware.  The caller must bound
the travel; a missing or failed sensor must never produce an unbounded motor
run.
"""

from __future__ import annotations

from dataclasses import dataclass
from time import monotonic
from typing import Protocol

from sensors.ir_home import HomeSensor


class HomingStepper(Protocol):
    def move_steps(self, steps: int, direction: int = 0) -> None:
        """Move a bounded number of steps and return with the driver disabled."""


def _move_one_step_and_check(stepper: HomingStepper, sensor: HomeSensor, direction: int) -> bool:
    observed = getattr(stepper, "move_step_observed", None)
    if callable(observed):
        return bool(observed(direction, sensor.is_home))
    stepper.move_steps(1, direction)
    return sensor.is_home()


class HomingError(RuntimeError):
    """Raised when the home reference is not found within the safety bound."""


@dataclass(frozen=True)
class HomingResult:
    reached_home: bool
    steps_taken: int
    already_home: bool


def home_stepper(
    stepper: HomingStepper,
    sensor: HomeSensor,
    *,
    direction: int = 0,
    max_steps: int = 400,
) -> HomingResult:
    """Move one step at a time until the active-high home input is reached.

    The sensor is sampled before motion and during each pulse. ``max_steps``
    is a hard travel bound independent of the motor's effective steps per
    revolution, and ``HomingError`` indicates that the reference was not found.
    """

    if direction not in (0, 1):
        raise ValueError("direction must be 0 or 1")
    if max_steps <= 0:
        raise ValueError("max_steps must be positive")

    if sensor.is_home():
        return HomingResult(reached_home=True, steps_taken=0, already_home=True)

    for steps_taken in range(1, max_steps + 1):
        if _move_one_step_and_check(stepper, sensor, direction):
            return HomingResult(
                reached_home=True,
                steps_taken=steps_taken,
                already_home=False,
            )

    raise HomingError(f"home not detected within {max_steps} steps")


def home_stepper_for_seconds(
    stepper: HomingStepper,
    sensor: HomeSensor,
    *,
    direction: int = 0,
    seconds: float = 90.0,
    max_steps: int = 2000,
) -> HomingResult:
    """Search for home for a hard time-limited duration.

    This is intentionally bounded by both time and steps. It is useful while
    calibrating an unknown mechanical reduction, but it must not become the
    production homing policy until the effective steps/revolution is known.
    """

    if direction not in (0, 1):
        raise ValueError("direction must be 0 or 1")
    if seconds <= 0:
        raise ValueError("seconds must be positive")
    if max_steps <= 0:
        raise ValueError("max_steps must be positive")

    if sensor.is_home():
        return HomingResult(reached_home=True, steps_taken=0, already_home=True)

    deadline = monotonic() + seconds
    for steps_taken in range(1, max_steps + 1):
        if monotonic() >= deadline:
            break
        if _move_one_step_and_check(stepper, sensor, direction):
            return HomingResult(
                reached_home=True,
                steps_taken=steps_taken,
                already_home=False,
            )

    raise HomingError(
        f"home not detected within {seconds:g} seconds or {max_steps} steps"
    )
