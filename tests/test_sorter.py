import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# Add raspberry-pi/app to import path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "raspberry-pi" / "app"))

from config import SorterConfig, load_config
from sorting.positioning import BinPositionPlanner, SorterPositionController
from sensors.ir_home import MockHomeSensor
from sensors.ultrasonic import MockUltrasonicSensor
from object_detection.detector import ObjectPresenceDetector
from camera.camera import MockCamera
from motors.servo import MockServo, ServoGate, GateConfig
from sorter.machine import AutonomousSorter, SorterState
from ai.inference import Prediction
from image_retention import ImageRetentionManager


class DummyStepper:
    def __init__(self):
        self.moves = []

    def move_steps(self, steps: int, direction: int = 0):
        self.moves.append((steps, direction))


class DummyModel:
    model_version = "v1-test"

    def __init__(self, category: str = "PLASTIC", confidence: float = 0.95):
        self.category = category
        self.confidence = confidence

    def predict(self, _path: Path) -> Prediction:
        return Prediction(
            category=self.category,
            confidence=self.confidence,
            model_version=self.model_version,
            inference_time_ms=12.5,
            timestamp="2026-09-01T12:00:00+00:00",
        )


class DummyFirebase:
    def __init__(self):
        self.sets = {}
        self.updates = {}
        self.reads = {}
        self.uploaded_temp = []
        self.retained = []
        self.deleted_temp = []
        self.configured = True

    def publish_status(self, device_id: str, status: dict):
        self.sets[f"devices/{device_id}/status"] = status

    def submit_set(self, path: str, value: dict):
        self.sets[path] = value

    def submit_update(self, path: str, value: dict):
        self.updates[path] = value

    def read(self, path: str):
        return self.reads.get(path)

    def submit_upload_temporary_image(self, local_path, device_id: str, event_id: str):
        self.uploaded_temp.append((str(local_path), device_id, event_id))

    def submit_retain_image(self, device_id: str, event_id: str, corrected: str, local_path):
        self.retained.append((device_id, event_id, corrected, str(local_path)))

    def submit_delete_temporary_image(self, device_id: str, event_id: str):
        self.deleted_temp.append((device_id, event_id))


class TestSorterSuite(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config = SorterConfig(
            data_dir=self.temp_dir,
            steps_per_revolution=600,
            forward_direction=1,
            trigger_distance_cm=7.0,
            minimum_distance_cm=1.5,
            presence_samples=2,
            clear_samples=2,
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_bin_position_planner(self):
        planner = BinPositionPlanner(
            bin_order=("BIODEGRADABLE", "PLASTIC", "METAL", "OTHER"),
            steps_per_revolution=600,
            forward_direction=1,
        )
        self.assertEqual(planner.steps_per_stop, 150)
        self.assertEqual(planner.stop_for("PLASTIC"), 1)
        self.assertEqual(planner.stop_for("METAL"), 2)

        # Move from 0 (BIODEGRADABLE) to 1 (PLASTIC) -> 1 stop forward = 150 steps
        plan1 = planner.plan("PLASTIC", 0)
        self.assertEqual(plan1.steps, 150)
        self.assertEqual(plan1.direction, 1)

        # Move from 0 (BIODEGRADABLE) to 3 (OTHER) -> shortest is -1 stop = 150 steps reverse (dir 0)
        plan2 = planner.plan("OTHER", 0)
        self.assertEqual(plan2.steps, 150)
        self.assertEqual(plan2.direction, 0)

        # Move from 0 (BIODEGRADABLE) to 2 (METAL) -> 2 stops tie -> uses forward_direction (dir 1)
        plan3 = planner.plan("METAL", 0)
        self.assertEqual(plan3.steps, 300)
        self.assertEqual(plan3.direction, 1)

    def test_position_controller_homing_and_movement(self):
        stepper = DummyStepper()
        # Sensor already at home
        home = MockHomeSensor([True])
        planner = BinPositionPlanner(steps_per_revolution=600)
        controller = SorterPositionController(stepper, home, planner)

        self.assertFalse(controller.calibrated)
        controller.calibrate()
        self.assertTrue(controller.calibrated)
        self.assertEqual(controller.current_stop, 0)
        self.assertEqual(len(stepper.moves), 0)

        # Move to PLASTIC (stop 1) -> 150 steps
        controller.move_to("PLASTIC")
        self.assertEqual(controller.current_stop, 1)
        self.assertEqual(len(stepper.moves), 1)
        self.assertEqual(stepper.moves[0], (150, 1))

    def test_object_presence_detector_debounce(self):
        sensor = MockUltrasonicSensor([15.0, 5.0, 5.0, 5.0, 20.0, 20.0])
        detector = ObjectPresenceDetector(
            sensor=sensor,
            present_threshold_cm=7.0,
            min_distance_cm=1.5,
            present_samples=2,
            clear_samples=2,
        )

        r1 = detector.poll()  # 15cm (clear)
        self.assertFalse(r1.present)

        r2 = detector.poll()  # 5cm (present count 1)
        self.assertFalse(r2.present)

        r3 = detector.poll()  # 5cm (present count 2 -> triggered!)
        self.assertTrue(r3.present)

        r4 = detector.poll()  # 5cm (remains present)
        self.assertTrue(r4.present)

        r5 = detector.poll()  # 20cm (clear count 1)
        self.assertTrue(r5.present)

        r6 = detector.poll()  # 20cm (clear count 2 -> cleared!)
        self.assertFalse(r6.present)

    def test_autonomous_sorter_full_cycle(self):
        stepper = DummyStepper()
        home = MockHomeSensor([True])
        u1 = MockUltrasonicSensor([5.0, 5.0, 25.0, 25.0])
        u3 = MockUltrasonicSensor([18.5])
        camera = MockCamera()
        model = DummyModel("PLASTIC", 0.98)
        servo = MockServo()
        servo.start()
        gate = ServoGate(servo, GateConfig(settle_seconds=0.0))
        firebase = DummyFirebase()
        retention = ImageRetentionManager(self.config, firebase)
        position = SorterPositionController(stepper, home)
        detector = ObjectPresenceDetector(
            u1,
            present_threshold_cm=7.0,
            present_samples=2,
            clear_samples=2,
        )

        machine = AutonomousSorter(
            config=self.config,
            detector=detector,
            camera=camera,
            model=model,
            position=position,
            gate=gate,
            bin_sensor=u3,
            firebase=firebase,
            retention=retention,
        )

        machine.start()
        self.assertEqual(machine.state, SorterState.READY)

        # Tick 1: U1 = 5.0 (sample 1) -> not triggered yet
        t1 = machine.tick()
        self.assertIsNone(t1)

        # Tick 2: U1 = 5.0 (sample 2) -> object detected & sorting cycle runs!
        t2 = machine.tick()
        self.assertIsNotNone(t2)
        self.assertEqual(t2["status"], "sorted")
        self.assertEqual(t2["detected_class"], "PLASTIC")
        self.assertEqual(t2["selected_bin"], "PLASTIC")
        self.assertEqual(t2["bin_distance_cm"], 18.5)
        self.assertEqual(machine.state, SorterState.WAITING_FOR_CLEAR)

        # Tick 3: U1 = 25.0 (clear sample 1) -> still waiting
        t3 = machine.tick()
        self.assertIsNone(t3)
        self.assertEqual(machine.state, SorterState.WAITING_FOR_CLEAR)

        # Tick 4: U1 = 25.0 (clear sample 2) -> returns to READY
        t4 = machine.tick()
        self.assertIsNone(t4)
        self.assertEqual(machine.state, SorterState.READY)

        machine.close()

    def test_image_retention_feedback_flow(self):
        firebase = DummyFirebase()
        retention = ImageRetentionManager(self.config, firebase)
        retention.start()

        event_id = "test-event-123"
        temp_img = self.config.temp_images_dir / f"{event_id}.jpg"
        temp_img.write_text("fake image content")

        retention.register(
            event_id=event_id,
            image_path=temp_img,
            prediction="PLASTIC",
            timestamp="2026-09-01T12:00:00+00:00",
        )
        self.assertTrue(temp_img.exists())

        # Simulate user providing feedback "incorrect" -> "METAL"
        firebase.reads[f"devices/{self.config.device_id}/feedback/{event_id}"] = {
            "status": "incorrect",
            "corrected_category": "METAL",
        }

        retention.process_once()

        # Image should be moved into feedback/METAL/ directory
        feedback_metal_dir = self.config.feedback_images_dir / "METAL"
        retained_files = list(feedback_metal_dir.glob("*.jpg"))
        self.assertEqual(len(retained_files), 1)
        self.assertIn("METAL", retained_files[0].name)
        self.assertFalse(temp_img.exists())

        retention.close()


if __name__ == "__main__":
    unittest.main()
