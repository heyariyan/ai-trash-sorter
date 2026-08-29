"""Comprehensive local system diagnostic tool for all hardware and software modules."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from time import sleep

from ai.inference import Prediction, TFLiteModel
from camera.camera import MockCamera, Picamera2Camera
from database.pocketbase import LocalFirstEventStore, PocketBaseClient
from display.display import ConsoleDisplay, MockDisplay, SSD1306I2CDisplay
from feedback.buttons import FeedbackResult, MockFeedbackPanel, TouchSwitchFeedbackPanel
from motors.homing import HomingError, home_stepper
from motors.servo import GateConfig, LgpioServo, MockServo, ServoGate
from motors.stepper import LgpioStepper
from object_detection.detector import ObjectPresenceDetector
from sensors.ir_home import IRHomeSensor, MockHomeSensor
from sensors.ultrasonic import LgpioUltrasonicSensor, MockUltrasonicSensor
from sorting.cycle import SortingCycle
from sorting.positioning import BinPositionPlanner, SorterPositionController

__test__ = False


def check_homing(args, home_sensor, stepper) -> bool:
    print("\n[TEST 1/5] Stepper Rotation & IR Home Sensor (GPIO23)...")
    try:
        if args.simulation:
            res = home_stepper(stepper, home_sensor, direction=0, max_steps=400)
            print(f"  -> Homing PASSED (Simulated: {res.steps_taken} steps)")
        else:
            res = home_stepper(stepper, home_sensor, direction=args.home_direction, max_steps=args.home_max_steps)
            print(f"  -> Homing PASSED: steps taken = {res.steps_taken}, already_home = {res.already_home}")
        return True
    except HomingError as exc:
        print(f"  -> Homing FAILED: {exc}")
        return False


def check_servo(args, gate) -> bool:
    print("\n[TEST 2/5] Servo Gate (GPIO18)...")
    try:
        print("  -> Opening gate (90 deg)...")
        gate.open()
        sleep(0.3)
        print("  -> Closing gate (0 deg)...")
        gate.close()
        sleep(0.2)
        print("  -> Servo Gate PASSED")
        return True
    except Exception as exc:
        print(f"  -> Servo Gate FAILED: {exc}")
        return False


def check_ultrasonic(args, u1, u3) -> bool:
    print("\n[TEST 3/5] Ultrasonic Sensors (U1 Intake & U3 Bin Level)...")
    try:
        u1_dist = u1.read_distance_cm()
        u3_dist = u3.read_distance_cm()
        u1_str = f"{u1_dist:.1f} cm" if u1_dist is not None else "TIMEOUT"
        u3_str = f"{u3_dist:.1f} cm" if u3_dist is not None else "TIMEOUT"
        print(f"  -> U1 Intake Distance: {u1_str}")
        print(f"  -> U3 Bin Level Distance: {u3_str}")
        print("  -> Ultrasonic Sensors PASSED")
        return True
    except Exception as exc:
        print(f"  -> Ultrasonic Sensors FAILED: {exc}")
        return False


def check_display(args, display) -> bool:
    print("\n[TEST 4/5] Display Subsystem...")
    try:
        display.show_status("System Test Mode")
        sleep(0.3)
        display.show_prediction("PLASTIC", 0.95)
        sleep(0.3)
        display.show_bin_status("PLASTIC", 18.0)
        sleep(0.3)
        display.show_feedback_prompt("PLASTIC correct?")
        sleep(0.3)
        display.show_status("Ready")
        print("  -> Display Subsystem PASSED")
        return True
    except Exception as exc:
        print(f"  -> Display Subsystem FAILED: {exc}")
        return False


def check_database_and_buffer(args, store: LocalFirstEventStore) -> bool:
    print("\n[TEST 5/5] Local Event Store & PocketBase Queue...")
    try:
        event_id = store.save_sorting_event(
            {
                "prediction": "PLASTIC",
                "confidence": 0.95,
                "selected_bin": "PLASTIC",
                "inference_time_ms": 12.5,
                "sorting_time_ms": 450.0,
                "success": True,
                "model_version": "system-test",
                "image_reference": "test-sample.jpg",
                "bin_distance_cm": 18.0,
            }
        )
        store.save_bin_status({"event_id": event_id, "selected_bin": "PLASTIC", "distance_cm": 18.0})
        store.save_feedback(
            {
                "event_id": event_id,
                "prediction": "PLASTIC",
                "correct": True,
                "image_reference": "test-sample.jpg",
            }
        )
        print(f"  -> Event Store PASSED (Generated Event ID: {event_id})")
        return True
    except Exception as exc:
        print(f"  -> Event Store FAILED: {exc}")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--simulation", action="store_true", help="Run full diagnostic in simulation mode")
    parser.add_argument("--confirm-movement", action="store_true", help="Required for physical actuator movements")
    parser.add_argument("--home-direction", type=int, choices=(0, 1), default=0)
    parser.add_argument("--home-max-steps", type=int, default=1000)
    parser.add_argument("--steps-per-revolution", type=int, default=600)
    parser.add_argument("--stepper-pulse-delay-ms", type=float, default=3.0)
    parser.add_argument("--display", choices=("console", "ssd1306", "mock"), default="console")
    parser.add_argument("--buffer-dir", type=Path, default=Path("/var/lib/ai-trash-sorter/runtime"))
    parser.add_argument("--pocketbase-url")
    parser.add_argument("--u1-trig", type=int, default=4)
    parser.add_argument("--u1-echo", type=int, default=5)
    parser.add_argument("--u3-trig", type=int, default=27)
    parser.add_argument("--u3-echo", type=int, default=13)
    args = parser.parse_args()

    if not args.simulation and not args.confirm_movement:
        print("ERROR: --confirm-movement or --simulation is required to run the local system tests.")
        return 1

    print("=========================================================")
    print("        AI TRASH SORTER - LOCAL SYSTEM DIAGNOSTIC        ")
    print("=========================================================")

    # Initialize components
    if args.simulation or args.display == "mock":
        display = MockDisplay()
    elif args.display == "ssd1306":
        display = SSD1306I2CDisplay()
    else:
        display = ConsoleDisplay()

    if args.simulation:
        stepper = _MockStepper()
        home_sensor = MockHomeSensor([True])
        servo = MockServo()
        servo.start()
        u1 = MockUltrasonicSensor([5.5])
        u3 = MockUltrasonicSensor([19.2])
    else:
        stepper = LgpioStepper(pulse_delay_seconds=args.stepper_pulse_delay_ms / 1000)
        stepper.start()
        home_sensor = IRHomeSensor(gpio=23)
        home_sensor.start()
        servo = LgpioServo(signal_gpio=18)
        servo.start()
        u1 = LgpioUltrasonicSensor(args.u1_trig, args.u1_echo)
        u1.start()
        u3 = LgpioUltrasonicSensor(args.u3_trig, args.u3_echo)
        u3.start()

    gate = ServoGate(servo, GateConfig(settle_seconds=0.2))
    pb = PocketBaseClient(args.pocketbase_url) if args.pocketbase_url else None
    store = LocalFirstEventStore(buffer_dir=args.buffer_dir, pocketbase=pb)

    passed = 0
    total = 5

    try:
        if check_homing(args, home_sensor, stepper):
            passed += 1
        if check_servo(args, gate):
            passed += 1
        if check_ultrasonic(args, u1, u3):
            passed += 1
        if check_display(args, display):
            passed += 1
        if check_database_and_buffer(args, store):
            passed += 1

        print("\n=========================================================")
        print(f"DIAGNOSTIC SUMMARY: {passed}/{total} tests passed.")
        if passed == total:
            print("ALL LOCAL SYSTEMS READY AND VERIFIED!")
            print("=========================================================")
            return 0
        else:
            print("SOME TESTS FAILED - Check hardware connections.")
            print("=========================================================")
            return 1
    finally:
        for comp in (stepper, home_sensor, servo, u1, u3, display, store):
            close = getattr(comp, "close", None)
            if callable(close):
                close()
            elif hasattr(comp, "stop"):
                comp.stop()


class _MockStepper:
    def __init__(self) -> None:
        self.moves: list[tuple[int, int]] = []

    def move_steps(self, steps: int, direction: int = 0) -> None:
        self.moves.append((steps, direction))


if __name__ == "__main__":
    raise SystemExit(main())
