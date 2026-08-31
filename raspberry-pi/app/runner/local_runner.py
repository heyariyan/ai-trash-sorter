"""Fast local appliance loop for offline sorting.

The loop is local-first: U1 detects an item, the warm camera captures, the
warm model predicts, the calibrated carousel moves by the shortest path, the
gate opens/closes, U3 records a post-drop bin measurement, feedback is
collected, and records are written locally with optional async PocketBase sync.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from time import monotonic, sleep
from typing import Sequence

from ai.inference import Prediction, TFLiteModel
from camera.camera import MockCamera, Picamera2Camera
from database.pocketbase import LocalFirstEventStore, PocketBaseClient
from display.display import ConsoleDisplay, SSD1306I2CDisplay
from feedback.buttons import FeedbackResult, MockFeedbackPanel, TouchSwitchFeedbackPanel
from motors.servo import GateConfig, LgpioServo, MockServo, ServoGate
from motors.stepper import LgpioStepper
from object_detection.detector import ObjectPresenceDetector
from sensors.ir_home import IRHomeSensor, MockHomeSensor
from sensors.ultrasonic import LgpioUltrasonicSensor, MockUltrasonicSensor
from sorting.cycle import SortingCycle
from sorting.positioning import DEFAULT_BIN_ORDER, BinPositionPlanner, SorterPositionController


@dataclass(frozen=True)
class RuntimeConfig:
    device_id: str = "rpi-local"
    capture_dir: Path = Path("/var/lib/ai-trash-sorter/images")
    buffer_dir: Path = Path("/var/lib/ai-trash-sorter/runtime")
    presence_threshold_cm: float = 7.0
    min_presence_cm: float = 1.5
    presence_samples: int = 2
    clear_samples: int = 2
    poll_seconds: float = 0.05
    feedback_timeout_seconds: float = 8.0
    post_drop_settle_seconds: float = 0.2
    steps_per_revolution: int = 600
    stepper_pulse_delay_seconds: float = 0.003
    home_direction: int = 0
    home_max_steps: int = 1000
    bin_order: tuple[str, ...] = DEFAULT_BIN_ORDER
    servo_closed_angle: float = 0.0
    servo_open_angle: float = 90.0
    servo_reverse: bool = True


class StaticModel:
    """Simulation model used only when no real TFLite file is provided."""

    def __init__(self, category: str = "PLASTIC") -> None:
        self.category = category

    def predict(self, image_path: Path) -> Prediction:
        return Prediction(
            category=self.category,
            confidence=0.99,
            model_version="simulation",
            inference_time_ms=0.0,
            timestamp="simulation",
        )


class FastLocalSorterRunner:
    """Compose the full local sorting path with hardware behind adapters."""

    def __init__(
        self,
        *,
        config: RuntimeConfig,
        presence_detector: ObjectPresenceDetector,
        camera,
        model,
        position_controller: SorterPositionController,
        gate: ServoGate,
        display,
        feedback_panel,
        event_store: LocalFirstEventStore,
        bin_status_sensor=None,
    ) -> None:
        self.config = config
        self.presence_detector = presence_detector
        self.camera = camera
        self.model = model
        self.position_controller = position_controller
        self.gate = gate
        self.display = display
        self.feedback_panel = feedback_panel
        self.event_store = event_store
        self.bin_status_sensor = bin_status_sensor
        self._calibration_requested = False

    def request_calibration(self) -> None:
        """Request calibration before the next cycle, for the app or API."""

        self._calibration_requested = True

    def start(self) -> None:
        self.display.show_status("Starting")
        self.camera.start()
        self.gate.close()
        try:
            self.calibrate(force=True)
        except Exception as exc:
            self.display.show_error(f"Homing: {exc}")
            sleep(1.0)
        self.display.show_status("Ready")

    def calibrate(self, *, force: bool = False) -> None:
        if self.position_controller.calibrated and not force:
            return
        self.display.show_status("Calibrating")
        try:
            self.position_controller.calibrate(
                home_direction=self.config.home_direction,
                max_home_steps=self.config.home_max_steps,
            )
            self._calibration_requested = False
            self.display.show_status("Home 0 Ready")
        except Exception as exc:
            self.display.show_error(f"Homing: {exc}")
            raise

    def wait_for_clear(self, *, timeout_seconds: float = 2.0) -> None:
        """Wait until the intake chute is cleared of objects."""
        started = monotonic()
        while monotonic() - started < timeout_seconds:
            reading = self.presence_detector.poll()
            if not reading.present:
                return
            sleep(self.config.poll_seconds)

    def wait_for_object(self, *, timeout_seconds: float | None = None):
        started = monotonic()
        while timeout_seconds is None or monotonic() - started < timeout_seconds:
            reading = self.presence_detector.poll()
            if reading.present:
                return reading
            sleep(self.config.poll_seconds)
        return None

    def _capture_path(self) -> Path:
        timestamp = int(monotonic() * 1000)
        return self.config.capture_dir / f"capture-{timestamp}.jpg"

    def run_once(self, *, wait_timeout_seconds: float | None = None) -> dict:
        if (
            self._calibration_requested
            or not self.position_controller.calibrated
            or (self.event_store and self.event_store.check_calibration_trigger())
        ):
            self.calibrate(force=True)

        detect_started = monotonic()
        presence = self.wait_for_object(timeout_seconds=wait_timeout_seconds)
        if presence is None:
            return {"status": "timeout_waiting_for_object"}
        detection_ms = round((monotonic() - detect_started) * 1000, 3)

        self.display.show_status("Capturing")
        capture = self.camera.capture(self._capture_path())

        cycle = SortingCycle(self.model, self.position_controller, self.gate)
        result = cycle.run(
            capture.path,
            on_prediction=lambda prediction: self.display.show_prediction(
                prediction.category,
                prediction.confidence,
            ),
        )
        prediction = result.prediction

        bin_distance_cm = None
        if self.bin_status_sensor is not None:
            sleep(self.config.post_drop_settle_seconds)
            bin_distance_cm = self.bin_status_sensor.read_distance_cm()
            self.display.show_bin_status(result.position_plan.category, bin_distance_cm)

        event_id = self.event_store.save_sorting_event(
            {
                "prediction": prediction.category,
                "confidence": prediction.confidence,
                "selected_bin": result.position_plan.category,
                "inference_time_ms": prediction.inference_time_ms,
                "sorting_time_ms": result.timings_ms["total_cycle_ms"],
                "success": True,
                "model_version": prediction.model_version,
                "image_reference": str(capture.path),
                "camera_capture_ms": capture.capture_time_ms,
                "sensor_detection_ms": detection_ms,
                "bin_distance_cm": bin_distance_cm,
                "position_plan": asdict(result.position_plan),
            }
        )

        if bin_distance_cm is not None:
            self.event_store.save_bin_status(
                {
                    "event_id": event_id,
                    "selected_bin": result.position_plan.category,
                    "distance_cm": bin_distance_cm,
                }
            )

        feedback = self.feedback_panel.wait_for_feedback(
            prediction=prediction.category,
            labels=self.config.bin_order,
            display=self.display,
            timeout_seconds=self.config.feedback_timeout_seconds,
        )
        self._save_feedback(event_id, prediction, feedback, capture.path)
        
        # Ensure chute is clear before returning to Ready
        self.wait_for_clear(timeout_seconds=2.0)
        self.display.show_status("Ready")

        capture_data = asdict(capture)
        capture_data["path"] = str(capture_data["path"])
        return {
            "status": "sorted",
            "event_id": event_id,
            "presence": asdict(presence),
            "capture": capture_data,
            "prediction": asdict(prediction),
            "position": asdict(result.position_plan),
            "bin_distance_cm": bin_distance_cm,
            "feedback": asdict(feedback),
            "timings_ms": {
                "sensor_detection_ms": detection_ms,
                "camera_capture_ms": capture.capture_time_ms,
                **result.timings_ms,
            },
        }

    def _save_feedback(
        self,
        event_id: str,
        prediction: Prediction,
        feedback: FeedbackResult,
        image_path: Path,
    ) -> None:
        if feedback.correct is None and feedback.timed_out:
            return
        self.event_store.save_feedback(
            {
                "event_id": event_id,
                "prediction": prediction.category,
                "correct": feedback.correct,
                "corrected_label": feedback.corrected_label,
                "image_reference": str(image_path),
            }
        )

    def close(self) -> None:
        servo = getattr(self.gate, "servo", None)
        for component in (
            self.camera,
            self.position_controller.stepper,
            self.position_controller.home_sensor,
            self.bin_status_sensor,
            self.feedback_panel,
            servo,
            self.display,
            self.event_store,
        ):
            close = getattr(component, "close", None)
            if callable(close):
                close()
                continue
            stop = getattr(component, "stop", None)
            if callable(stop):
                stop()


def _build_runner(args: argparse.Namespace) -> FastLocalSorterRunner:
    config = RuntimeConfig(
        device_id=args.device_id,
        capture_dir=args.capture_dir,
        buffer_dir=args.buffer_dir,
        presence_threshold_cm=args.presence_threshold_cm,
        min_presence_cm=args.min_presence_cm,
        presence_samples=args.presence_samples,
        clear_samples=args.clear_samples,
        steps_per_revolution=args.steps_per_revolution,
        stepper_pulse_delay_seconds=args.stepper_pulse_delay_ms / 1000,
        feedback_timeout_seconds=args.feedback_timeout_seconds,
        post_drop_settle_seconds=args.post_drop_settle_seconds,
        servo_closed_angle=args.servo_closed_angle,
        servo_open_angle=args.servo_open_angle,
        servo_reverse=not args.servo_normal_direction,
    )
    display = SSD1306I2CDisplay() if args.display == "ssd1306" else ConsoleDisplay()

    if args.simulation:
        presence_sensor = MockUltrasonicSensor([5.0])
        bin_status_sensor = MockUltrasonicSensor([18.0])
        camera = MockCamera()
        stepper = _MockStepper()
        home_sensor = MockHomeSensor([True])
        servo = MockServo()
        servo.start()
        feedback_panel = MockFeedbackPanel([FeedbackResult(correct=True)])
        model = StaticModel(args.simulation_category)
    else:
        if not args.confirm_movement:
            raise SystemExit("--confirm-movement is required for real stepper/servo control")
        presence_sensor = LgpioUltrasonicSensor(args.u1_trig, args.u1_echo)
        presence_sensor.start()
        bin_status_sensor = LgpioUltrasonicSensor(args.bin_trig, args.bin_echo)
        bin_status_sensor.start()
        camera = Picamera2Camera()
        stepper = LgpioStepper(pulse_delay_seconds=config.stepper_pulse_delay_seconds)
        stepper.start()
        home_sensor = IRHomeSensor()
        home_sensor.start()
        servo = LgpioServo(signal_gpio=args.servo_gpio, reverse=config.servo_reverse)
        servo.start()
        feedback_panel = TouchSwitchFeedbackPanel(active_level=args.touch_active_level)
        feedback_panel.start()
        default_model = Path("/home/ariyan/ai-trash-sorter-test/model/waste-mobilenet-taco-kaggle-v1.tflite")
        model_path = args.model or (default_model if default_model.is_file() else None)
        model = TFLiteModel(model_path) if model_path is not None else StaticModel("PLASTIC")

    planner = BinPositionPlanner(
        bin_order=config.bin_order,
        steps_per_revolution=config.steps_per_revolution,
    )
    position = SorterPositionController(stepper, home_sensor, planner)
    gate = ServoGate(
        servo,
        GateConfig(
            closed_angle=config.servo_closed_angle,
            open_angle=config.servo_open_angle,
            settle_seconds=args.gate_settle_seconds,
        ),
    )
    pb = PocketBaseClient(args.pocketbase_url) if args.pocketbase_url else None
    store = LocalFirstEventStore(
        buffer_dir=config.buffer_dir,
        pocketbase=pb,
        device_id=config.device_id,
    )
    detector = ObjectPresenceDetector(
        presence_sensor,
        present_threshold_cm=config.presence_threshold_cm,
        min_distance_cm=config.min_presence_cm,
        present_samples=config.presence_samples,
        clear_samples=config.clear_samples,
    )
    return FastLocalSorterRunner(
        config=config,
        presence_detector=detector,
        camera=camera,
        model=model,
        position_controller=position,
        gate=gate,
        display=display,
        feedback_panel=feedback_panel,
        event_store=store,
        bin_status_sensor=bin_status_sensor,
    )


class _MockStepper:
    def __init__(self) -> None:
        self.moves: list[tuple[int, int]] = []

    def move_steps(self, steps: int, direction: int = 0) -> None:
        self.moves.append((steps, direction))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path)
    parser.add_argument("--simulation", action="store_true")
    parser.add_argument("--simulation-category", default="PLASTIC")
    parser.add_argument("--confirm-movement", action="store_true")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--calibrate-now", action="store_true", help="Calibrate home position immediately and exit")
    parser.add_argument("--device-id", default="rpi-local")
    parser.add_argument("--capture-dir", type=Path, default=Path("/var/lib/ai-trash-sorter/images"))
    parser.add_argument("--buffer-dir", type=Path, default=Path("/var/lib/ai-trash-sorter/runtime"))
    parser.add_argument("--presence-threshold-cm", type=float, default=7.0)
    parser.add_argument("--min-presence-cm", type=float, default=1.5)
    parser.add_argument("--presence-samples", type=int, default=2)
    parser.add_argument("--clear-samples", type=int, default=2)
    parser.add_argument("--steps-per-revolution", type=int, default=600)
    parser.add_argument("--stepper-pulse-delay-ms", type=float, default=3.0)
    parser.add_argument("--servo-gpio", type=int, default=18)
    parser.add_argument("--servo-closed-angle", type=float, default=0.0)
    parser.add_argument("--servo-open-angle", type=float, default=90.0)
    parser.add_argument("--servo-normal-direction", action="store_true")
    parser.add_argument("--gate-settle-seconds", type=float, default=0.2)
    parser.add_argument("--post-drop-settle-seconds", type=float, default=0.2)
    parser.add_argument("--feedback-timeout-seconds", type=float, default=8.0)
    parser.add_argument("--pocketbase-url")
    parser.add_argument("--display", choices=("console", "ssd1306"), default="console")
    parser.add_argument("--touch-active-level", type=int, choices=(0, 1), default=1)
    parser.add_argument("--u1-trig", type=int, default=4)
    parser.add_argument("--u1-echo", type=int, default=5)
    parser.add_argument("--bin-trig", type=int, default=27)
    parser.add_argument("--bin-echo", type=int, default=13)
    args = parser.parse_args(argv)

    if not args.simulation and args.model is None and not args.calibrate_now:
        parser.error("--model is required unless --simulation or --calibrate-now is used")

    runner = _build_runner(args)
    try:
        runner.start()
        if args.calibrate_now:
            print("Calibration complete. Home 0 verified.")
            return 0
        if args.once:
            result = runner.run_once()
            print(json.dumps(result, sort_keys=True))
        else:
            while True:
                result = runner.run_once()
                print(json.dumps(result, sort_keys=True))
    finally:
        runner.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
