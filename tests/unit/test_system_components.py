import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "raspberry-pi" / "app"))

from database.pocketbase import LocalFirstEventStore, PocketBaseClient  # noqa: E402
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


class SystemComponentsTests(unittest.TestCase):
    def test_calibration_trigger_file_causes_recalibration(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            buffer_dir = root / "runtime"
            buffer_dir.mkdir(parents=True, exist_ok=True)

            config = RuntimeConfig(
                capture_dir=root / "images",
                buffer_dir=buffer_dir,
                post_drop_settle_seconds=0,
                feedback_timeout_seconds=0.1,
                steps_per_revolution=600,
            )
            stepper = FakeStepper()
            home_sensor = MockHomeSensor([True, False, True])
            position = SorterPositionController(
                stepper,
                home_sensor,
                BinPositionPlanner(steps_per_revolution=600),
            )
            servo = MockServo()
            servo.start()
            display = MockDisplay()
            store = LocalFirstEventStore(buffer_dir=buffer_dir)

            runner = FastLocalSorterRunner(
                config=config,
                presence_detector=ObjectPresenceDetector(
                    MockUltrasonicSensor([5.0, 20.0, 5.0, 20.0]),
                    present_threshold_cm=7.0,
                    present_samples=1,
                ),
                camera=MockCamera(),
                model=StaticModel("PLASTIC"),
                position_controller=position,
                gate=ServoGate(servo, GateConfig(settle_seconds=0)),
                display=display,
                feedback_panel=MockFeedbackPanel([FeedbackResult(correct=True)]),
                event_store=store,
                bin_status_sensor=MockUltrasonicSensor([15.0, 15.0]),
            )

            runner.start()
            self.assertTrue(position.calibrated)

            # Cycle 1: normal run
            res1 = runner.run_once(wait_timeout_seconds=0.1)
            self.assertEqual(res1["status"], "sorted")

            # Create calibrate.trigger file
            trigger_file = buffer_dir / "calibrate.trigger"
            trigger_file.write_text("calibrate", encoding="utf-8")

            # Cycle 2: should detect trigger file and recalibrate
            res2 = runner.run_once(wait_timeout_seconds=0.1)
            self.assertEqual(res2["status"], "sorted")
            self.assertFalse(trigger_file.exists())  # trigger file was cleaned up

            runner.close()

    def test_request_calibration_method_triggers_calibration(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = RuntimeConfig(
                capture_dir=root / "images",
                buffer_dir=root / "runtime",
                post_drop_settle_seconds=0,
                feedback_timeout_seconds=0.1,
                steps_per_revolution=600,
            )
            stepper = FakeStepper()
            home_sensor = MockHomeSensor([True, True])
            position = SorterPositionController(
                stepper,
                home_sensor,
                BinPositionPlanner(steps_per_revolution=600),
            )
            servo = MockServo()
            servo.start()
            display = MockDisplay()
            store = LocalFirstEventStore(buffer_dir=config.buffer_dir)

            runner = FastLocalSorterRunner(
                config=config,
                presence_detector=ObjectPresenceDetector(
                    MockUltrasonicSensor([5.0, 5.0]),
                    present_threshold_cm=7.0,
                    present_samples=1,
                ),
                camera=MockCamera(),
                model=StaticModel("BIODEGRADABLE"),
                position_controller=position,
                gate=ServoGate(servo, GateConfig(settle_seconds=0)),
                display=display,
                feedback_panel=MockFeedbackPanel([FeedbackResult(correct=True)]),
                event_store=store,
            )

            runner.start()
            runner.request_calibration()
            self.assertTrue(runner._calibration_requested)

            res = runner.run_once(wait_timeout_seconds=0.1)
            self.assertEqual(res["status"], "sorted")
            self.assertFalse(runner._calibration_requested)
            runner.close()

    def test_correction_feedback_flow_saves_corrected_label_and_image(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = RuntimeConfig(
                capture_dir=root / "images",
                buffer_dir=root / "runtime",
                post_drop_settle_seconds=0,
                feedback_timeout_seconds=0.1,
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
            display = MockDisplay()
            store = LocalFirstEventStore(buffer_dir=config.buffer_dir)

            runner = FastLocalSorterRunner(
                config=config,
                presence_detector=ObjectPresenceDetector(
                    MockUltrasonicSensor([4.5]),
                    present_threshold_cm=7.0,
                    present_samples=1,
                ),
                camera=MockCamera(),
                model=StaticModel("OTHER"),
                position_controller=position,
                gate=ServoGate(servo, GateConfig(settle_seconds=0)),
                display=display,
                feedback_panel=MockFeedbackPanel(
                    [FeedbackResult(correct=False, corrected_label="METAL")]
                ),
                event_store=store,
                bin_status_sensor=MockUltrasonicSensor([21.0]),
            )

            runner.start()
            result = runner.run_once(wait_timeout_seconds=0.1)
            runner.close()

            self.assertEqual(result["prediction"]["category"], "OTHER")
            self.assertEqual(result["feedback"]["correct"], False)
            self.assertEqual(result["feedback"]["corrected_label"], "METAL")

            # Check feedback JSONL
            feedback_path = config.buffer_dir / "feedback.jsonl"
            self.assertTrue(feedback_path.exists())
            records = [json.loads(line) for line in feedback_path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["prediction"], "OTHER")
            self.assertEqual(records[0]["correct"], False)
            self.assertEqual(records[0]["corrected_label"], "METAL")
            self.assertTrue("capture-" in records[0]["image_reference"])


if __name__ == "__main__":
    unittest.main()
