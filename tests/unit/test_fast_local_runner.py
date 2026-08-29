import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "raspberry-pi" / "app"))

from database.pocketbase import LocalFirstEventStore  # noqa: E402
from display.display import MockDisplay  # noqa: E402
from feedback.buttons import FeedbackResult, MockFeedbackPanel  # noqa: E402
from motors.servo import GateConfig, MockServo, ServoGate  # noqa: E402
from object_detection.detector import ObjectPresenceDetector  # noqa: E402
from runner.local_runner import FastLocalSorterRunner, RuntimeConfig, StaticModel  # noqa: E402
from sensors import MockHomeSensor, MockUltrasonicSensor  # noqa: E402
from sorting.positioning import BinPositionPlanner, SorterPositionController  # noqa: E402
from camera.camera import MockCamera  # noqa: E402


class FakeStepper:
    def __init__(self) -> None:
        self.moves = []

    def move_steps(self, steps: int, direction: int = 0) -> None:
        self.moves.append((steps, direction))


class FastLocalRunnerTests(unittest.TestCase):
    def test_full_loop_records_event_bin_status_and_feedback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = RuntimeConfig(
                capture_dir=root / "images",
                buffer_dir=root / "runtime",
                post_drop_settle_seconds=0,
                feedback_timeout_seconds=1,
                steps_per_revolution=600,
            )
            stepper = FakeStepper()
            position = SorterPositionController(
                stepper,
                MockHomeSensor([True]),
                BinPositionPlanner(steps_per_revolution=600),
            )
            servo = MockServo()
            servo.start()
            runner = FastLocalSorterRunner(
                config=config,
                presence_detector=ObjectPresenceDetector(
                    MockUltrasonicSensor([5.0]),
                    present_threshold_cm=7.0,
                    present_samples=1,
                ),
                camera=MockCamera(),
                model=StaticModel("METAL"),
                position_controller=position,
                gate=ServoGate(servo, GateConfig(settle_seconds=0)),
                display=MockDisplay(),
                feedback_panel=MockFeedbackPanel(
                    [FeedbackResult(correct=False, corrected_label="PLASTIC")]
                ),
                event_store=LocalFirstEventStore(buffer_dir=config.buffer_dir),
                bin_status_sensor=MockUltrasonicSensor([22.5]),
            )

            runner.start()
            result = runner.run_once(wait_timeout_seconds=0.1)
            runner.close()

            self.assertEqual(result["status"], "sorted")
            self.assertEqual(result["prediction"]["category"], "METAL")
            self.assertEqual(result["position"]["steps"], 300)
            self.assertEqual(result["bin_distance_cm"], 22.5)
            self.assertEqual(stepper.moves, [(300, 1)])
            self.assertEqual(servo.positions, [0.0, 90.0, 0.0])

            events = (config.buffer_dir / "sorting-events.jsonl").read_text(encoding="utf-8")
            event = json.loads(events.splitlines()[0])
            self.assertEqual(event["prediction"], "METAL")
            self.assertEqual(event["selected_bin"], "METAL")
            self.assertEqual(event["bin_distance_cm"], 22.5)

            feedback = (config.buffer_dir / "feedback.jsonl").read_text(encoding="utf-8")
            feedback_record = json.loads(feedback.splitlines()[0])
            self.assertEqual(feedback_record["corrected_label"], "PLASTIC")

            # Check that display received status, prediction, bin_status, feedback, and ready
            display_actions = [msg[0] for msg in runner.display.messages]
            self.assertIn("prediction", display_actions)
            self.assertIn("bin_status", display_actions)
            self.assertIn("feedback", display_actions)
            self.assertEqual(runner.display.last_bin_status, ("METAL", 22.5))


if __name__ == "__main__":
    unittest.main()
