import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "raspberry-pi" / "app"))

from sensors import MockHomeSensor  # noqa: E402
from sorting import BinPositionPlanner, SorterPositionController  # noqa: E402


class FakeStepper:
    def __init__(self) -> None:
        self.moves: list[tuple[int, int]] = []

    def move_steps(self, steps: int, direction: int = 0) -> None:
        self.moves.append((steps, direction))


class PositioningTests(unittest.TestCase):
    def test_plastic_from_home_is_one_stop(self) -> None:
        planner = BinPositionPlanner(forward_direction=1)
        plan = planner.plan("plastic", current_stop=0)
        self.assertEqual((plan.target_stop, plan.signed_stops, plan.steps), (1, 1, 50))
        self.assertEqual(plan.direction, 1)

    def test_other_from_home_reverses_one_stop_instead_of_three(self) -> None:
        planner = BinPositionPlanner(forward_direction=1)
        plan = planner.plan("OTHER", current_stop=0)
        self.assertEqual((plan.target_stop, plan.signed_stops, plan.steps), (3, -1, 50))
        self.assertEqual(plan.direction, 0)

    def test_controller_requires_calibration_and_updates_after_success(self) -> None:
        stepper = FakeStepper()
        controller = SorterPositionController(stepper, MockHomeSensor([True]))
        with self.assertRaises(RuntimeError):
            controller.plan_for("METAL")
        result = controller.calibrate()
        self.assertTrue(result.already_home)
        plan = controller.move_to("METAL")
        self.assertEqual(plan.steps, 100)
        self.assertEqual(controller.current_stop, 2)
        self.assertEqual(stepper.moves, [(100, 1)])

    def test_failed_move_does_not_claim_target(self) -> None:
        class FailingStepper(FakeStepper):
            def move_steps(self, steps: int, direction: int = 0) -> None:
                raise RuntimeError("stall")

        controller = SorterPositionController(FailingStepper(), MockHomeSensor([True]))
        controller.calibrate()
        with self.assertRaises(RuntimeError):
            controller.move_to("PLASTIC")
        self.assertFalse(controller.calibrated)


if __name__ == "__main__":
    unittest.main()
