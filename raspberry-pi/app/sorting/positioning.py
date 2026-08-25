"""Shortest-path positioning for the four-bin sorter carousel.

The home sensor defines stop 0 at boot.  The default logical order is
BIODEGRADABLE, PLASTIC, METAL, OTHER at four equally spaced stops, but the
order and full-revolution step count are configurable because the mechanical
calibration is installation-specific.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from motors.homing import HomingResult, home_stepper
from sensors.ir_home import HomeSensor


DEFAULT_BIN_ORDER: Final[tuple[str, ...]] = (
    "BIODEGRADABLE",
    "PLASTIC",
    "METAL",
    "OTHER",
)


@dataclass(frozen=True)
class PositionPlan:
    """One shortest movement from the current stop to a target stop."""

    category: str
    current_stop: int
    target_stop: int
    signed_stops: int
    direction: int
    steps: int


class BinPositionPlanner:
    """Calculate shortest modular moves without touching GPIO."""

    def __init__(
        self,
        *,
        bin_order: tuple[str, ...] = DEFAULT_BIN_ORDER,
        steps_per_revolution: int = 200,
        forward_direction: int = 1,
    ) -> None:
        normalized = tuple(str(category).upper() for category in bin_order)
        if len(normalized) != 4 or len(set(normalized)) != 4:
            raise ValueError("bin_order must contain four unique categories")
        if steps_per_revolution <= 0 or steps_per_revolution % 4:
            raise ValueError("steps_per_revolution must be positive and divisible by 4")
        if forward_direction not in (0, 1):
            raise ValueError("forward_direction must be 0 or 1")
        self.bin_order = normalized
        self.steps_per_revolution = steps_per_revolution
        self.steps_per_stop = steps_per_revolution // len(normalized)
        self.forward_direction = forward_direction

    def stop_for(self, category: str) -> int:
        normalized = str(category).upper()
        try:
            return self.bin_order.index(normalized)
        except ValueError as exc:
            raise ValueError(f"unsupported bin category: {category!r}") from exc

    def plan(self, category: str, current_stop: int) -> PositionPlan:
        if current_stop not in range(len(self.bin_order)):
            raise ValueError("current_stop is outside the four-stop carousel")
        target_stop = self.stop_for(category)
        clockwise = (target_stop - current_stop) % len(self.bin_order)
        # A two-stop tie is deterministic: use the configured forward direction.
        signed_stops = clockwise if clockwise <= len(self.bin_order) // 2 else clockwise - len(self.bin_order)
        direction = self.forward_direction if signed_stops >= 0 else 1 - self.forward_direction
        return PositionPlan(
            category=str(category).upper(),
            current_stop=current_stop,
            target_stop=target_stop,
            signed_stops=signed_stops,
            direction=direction,
            steps=abs(signed_stops) * self.steps_per_stop,
        )


class SorterPositionController:
    """Own the calibrated logical stop and command bounded stepper moves."""

    def __init__(
        self,
        stepper,
        home_sensor: HomeSensor,
        planner: BinPositionPlanner | None = None,
    ) -> None:
        self.stepper = stepper
        self.home_sensor = home_sensor
        self.planner = planner or BinPositionPlanner()
        self.current_stop: int | None = None

    @property
    def calibrated(self) -> bool:
        return self.current_stop is not None

    def calibrate(self, *, home_direction: int = 0, max_home_steps: int = 400) -> HomingResult:
        """Home once at boot and establish logical stop 0."""

        result = home_stepper(
            self.stepper,
            self.home_sensor,
            direction=home_direction,
            max_steps=max_home_steps,
        )
        self.current_stop = 0
        return result

    def plan_for(self, category: str) -> PositionPlan:
        if self.current_stop is None:
            raise RuntimeError("sorter must be homed before selecting a bin")
        return self.planner.plan(category, self.current_stop)

    def move_to(self, category: str) -> PositionPlan:
        """Move to a category and update state only after the move succeeds."""

        plan = self.plan_for(category)
        if plan.steps:
            try:
                self.stepper.move_steps(plan.steps, plan.direction)
            except Exception:
                self.invalidate_position()
                raise
        self.current_stop = plan.target_stop
        return plan

    def invalidate_position(self) -> None:
        """Mark position unknown after an interrupted or failed physical move."""

        self.current_stop = None
