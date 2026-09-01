"""Production entry point for the autonomous AI trash sorter."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from time import sleep

from ai.inference import Prediction, TFLiteModel
from camera.camera import MockCamera, Picamera2Camera
from config import SorterConfig, load_config
from display.display import ConsoleDisplay, SSD1306I2CDisplay
from firebase_service import FirebaseService
from image_retention import ImageRetentionManager
from motors.servo import GateConfig, LgpioServo, MockServo, ServoGate
from motors.stepper import LgpioStepper
from object_detection.detector import ObjectPresenceDetector
from sensors.ir_home import IRHomeSensor, MockHomeSensor
from sensors.ultrasonic import LgpioUltrasonicSensor, MockUltrasonicSensor
from sorter.machine import AutonomousSorter
from sorting.positioning import BinPositionPlanner, SorterPositionController


class SimulationModel:
    model_version = "simulation"
    def __init__(self, category: str): self.category = category.upper()
    def predict(self, _path: Path) -> Prediction:
        return Prediction(self.category, 0.99, self.model_version, 0.0, "2026-01-01T00:00:00+00:00")


class SimulationStepper:
    def move_steps(self, _steps: int, _direction: int = 0) -> None: pass


def build_machine(config: SorterConfig, *, simulation: bool, simulation_category: str) -> AutonomousSorter:
    if simulation:
        camera, model = MockCamera(), SimulationModel(simulation_category)
        u1, u3, stepper, home = MockUltrasonicSensor([5.0, 5.0, 30.0]), MockUltrasonicSensor([20.0]), SimulationStepper(), MockHomeSensor([True])
        servo = MockServo(); servo.start()
    else:
        camera = Picamera2Camera(config.camera_width, config.camera_height, config.camera_warmup_seconds)
        model = TFLiteModel(config.model_path, config.model_metadata_path)
        u1 = LgpioUltrasonicSensor(config.u1_trigger_gpio, config.u1_echo_gpio); u1.start()
        u3 = LgpioUltrasonicSensor(config.u3_trigger_gpio, config.u3_echo_gpio); u3.start()
        stepper = LgpioStepper(config.step_gpio, config.direction_gpio, config.enable_gpio, config.reset_gpio, config.sleep_gpio, pulse_delay_seconds=config.step_pulse_seconds); stepper.start()
        home = IRHomeSensor(config.home_gpio, home_level=1); home.start()
        servo = LgpioServo(signal_gpio=config.servo_gpio, reverse=config.servo_reverse); servo.start()
    detector = ObjectPresenceDetector(u1, config.trigger_distance_cm, config.minimum_distance_cm, config.presence_samples, config.clear_samples)
    display = SSD1306I2CDisplay() if config.display == "ssd1306" else ConsoleDisplay()
    position = SorterPositionController(stepper, home, BinPositionPlanner(bin_order=config.bin_order, steps_per_revolution=config.steps_per_revolution, forward_direction=config.forward_direction))
    gate = ServoGate(servo, GateConfig(config.servo_closed_angle, config.servo_open_angle, config.gate_settle_seconds))
    firebase = FirebaseService(database_url=config.firebase_database_url, credentials_path=config.firebase_credentials_path, storage_bucket=config.firebase_storage_bucket)
    retention = ImageRetentionManager(config, firebase)
    return AutonomousSorter(config=config, detector=detector, camera=camera, model=model, position=position, gate=gate, bin_sensor=u3, firebase=firebase, retention=retention, display=display)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--simulation", action="store_true")
    parser.add_argument("--simulation-category", default="PLASTIC")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--confirm-actuators", action="store_true", help="required before any real stepper or servo command")
    args = parser.parse_args()
    if not args.simulation and not args.confirm_actuators:
        parser.error("real hardware is blocked; pass --confirm-actuators only after the mechanism is clear and safe")
    config = load_config(args.config)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    machine = build_machine(config, simulation=args.simulation, simulation_category=args.simulation_category)
    try:
        machine.start()
        if args.once:
            while True:
                result = machine.tick()
                if result: print(result); return 0
                sleep(config.poll_seconds)
        while True:
            machine.tick()
            sleep(config.poll_seconds)
    except KeyboardInterrupt:
        return 0
    finally:
        machine.close()


if __name__ == "__main__":
    raise SystemExit(main())
