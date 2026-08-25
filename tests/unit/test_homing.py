import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "raspberry-pi" / "app"))

from motors.homing import HomingError, home_stepper, home_stepper_for_seconds  # noqa: E402
from sensors import MockHomeSensor  # noqa: E402


class FakeStepper:
    def __init__(self) -> None:
        self.moves: list[tuple[int, int]] = []

    def move_steps(self, steps: int, direction: int = 0) -> None:
        self.moves.append((steps, direction))


class HomingTests(unittest.TestCase):
    def test_high_home_input_prevents_motion(self) -> None:
        stepper = FakeStepper()
        result = home_stepper(stepper, MockHomeSensor([True]), max_steps=10)
        self.assertTrue(result.reached_home)
        self.assertTrue(result.already_home)
        self.assertEqual(result.steps_taken, 0)
        self.assertEqual(stepper.moves, [])

    def test_moves_until_home_and_uses_requested_direction(self) -> None:
        stepper = FakeStepper()
        result = home_stepper(
            stepper,
            MockHomeSensor([False, False, True]),
            direction=1,
            max_steps=5,
        )
        self.assertTrue(result.reached_home)
        self.assertFalse(result.already_home)
        self.assertEqual(result.steps_taken, 2)
        self.assertEqual(stepper.moves, [(1, 1), (1, 1)])

    def test_missing_home_is_bounded(self) -> None:
        stepper = FakeStepper()
        with self.assertRaises(HomingError):
            home_stepper(stepper, MockHomeSensor([False]), max_steps=3)
        self.assertEqual(len(stepper.moves), 3)

    def test_rejects_invalid_bounds(self) -> None:
        with self.assertRaises(ValueError):
            home_stepper(FakeStepper(), MockHomeSensor([False]), max_steps=0)

    def test_timed_search_stops_when_sensor_reaches_home(self) -> None:
        stepper = FakeStepper()
        result = home_stepper_for_seconds(
            stepper,
            MockHomeSensor([False, True]),
            seconds=1,
            max_steps=10,
        )
        self.assertTrue(result.reached_home)
        self.assertEqual(result.steps_taken, 1)

    def test_timed_search_has_step_bound(self) -> None:
        with self.assertRaises(HomingError):
            home_stepper_for_seconds(
                FakeStepper(), MockHomeSensor([False]), seconds=1, max_steps=2
            )

    def test_observed_step_can_latch_a_brief_home_edge(self) -> None:
        class ObservedStepper(FakeStepper):
            def move_step_observed(self, direction, sample) -> bool:
                self.moves.append((1, direction))
                return sample()

        stepper = ObservedStepper()
        result = home_stepper(
            stepper, MockHomeSensor([False, True]), direction=1, max_steps=3
        )
        self.assertTrue(result.reached_home)
        self.assertEqual(result.steps_taken, 1)


if __name__ == "__main__":
    unittest.main()
