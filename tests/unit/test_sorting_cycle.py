import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "raspberry-pi" / "app"))

from sorting.cycle import SortingCycle  # noqa: E402
from sorting.positioning import BinPositionPlanner, SorterPositionController  # noqa: E402
from motors.servo import GateConfig, MockServo, ServoGate  # noqa: E402
from sensors import MockHomeSensor  # noqa: E402


class FakeStepper:
    def __init__(self) -> None:
        self.moves = []

    def move_steps(self, steps: int, direction: int = 0) -> None:
        self.moves.append((steps, direction))


class FakeModel:
    def __init__(self, category: str) -> None:
        self.category = category

    def predict(self, image_path: Path):
        return SimpleNamespace(
            category=self.category,
            confidence=0.9,
            model_version="test",
            inference_time_ms=1.0,
            timestamp="test",
        )


class SortingCycleTests(unittest.TestCase):
    def test_cycle_predicts_moves_and_closes_gate(self) -> None:
        stepper = FakeStepper()
        position = SorterPositionController(
            stepper, MockHomeSensor([True]), BinPositionPlanner(steps_per_revolution=200)
        )
        position.calibrate()
        servo = MockServo()
        servo.start()
        gate = ServoGate(servo, GateConfig(settle_seconds=0))
        result = SortingCycle(FakeModel("PLASTIC"), position, gate).run(Path("item.jpg"))
        self.assertEqual(result.prediction.category, "PLASTIC")
        self.assertEqual(result.position_plan.steps, 50)
        self.assertEqual(servo.positions, [90, 0])
        self.assertIn("total_cycle_ms", result.timings_ms)

    def test_cycle_requires_boot_calibration(self) -> None:
        position = SorterPositionController(FakeStepper(), MockHomeSensor([False]))
        servo = MockServo()
        servo.start()
        gate = ServoGate(servo, GateConfig(settle_seconds=0))
        with self.assertRaises(RuntimeError):
            SortingCycle(FakeModel("METAL"), position, gate).run(Path("item.jpg"))


if __name__ == "__main__":
    unittest.main()
