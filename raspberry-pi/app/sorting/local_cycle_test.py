"""Run bounded offline sorting cycles from existing Pi image files.

This test intentionally excludes the camera and ultrasonic sensors. Physical
stepper/servo movement requires ``--confirm-movement`` and an explicit measured
effective steps-per-revolution value.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ai.inference import TFLiteModel
from motors.homing import HomingError
from motors.servo import GateConfig, LgpioServo, ServoGate
from motors.stepper import LgpioStepper
from sensors.ir_home import IRHomeSensor

from .cycle import SortingCycle
from .positioning import BinPositionPlanner, SorterPositionController


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("images", nargs="+", type=Path)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--metadata", type=Path)
    parser.add_argument("--steps-per-revolution", type=int, required=True)
    parser.add_argument("--home-direction", type=int, choices=(0, 1), default=0)
    parser.add_argument("--home-max-steps", type=int, default=1000)
    parser.add_argument("--pulse-delay-ms", type=float, default=20.0)
    parser.add_argument("--confirm-movement", action="store_true")
    args = parser.parse_args()
    if args.steps_per_revolution <= 0 or args.steps_per_revolution % 4:
        raise SystemExit("steps-per-revolution must be positive and divisible by 4")
    if args.home_max_steps <= 0 or args.pulse_delay_ms <= 0:
        raise SystemExit("home-max-steps and pulse-delay-ms must be positive")
    if not args.confirm_movement:
        raise SystemExit("refusing combined actuator test; pass --confirm-movement")
    missing = [str(path) for path in args.images if not path.is_file()]
    if missing:
        raise SystemExit(f"image files not found: {', '.join(missing)}")

    model = TFLiteModel(args.model, args.metadata)
    stepper = LgpioStepper(pulse_delay_seconds=args.pulse_delay_ms / 1000)
    home_sensor = IRHomeSensor(gpio=23, home_level=1)
    planner = BinPositionPlanner(steps_per_revolution=args.steps_per_revolution)
    position = SorterPositionController(stepper, home_sensor, planner)
    servo = LgpioServo(signal_gpio=18, reverse=True)
    gate = ServoGate(servo, GateConfig(closed_angle=0, open_angle=90, settle_seconds=0.5))
    try:
        stepper.start()
        home_sensor.start()
        servo.start()
        # Calibration is always first and must establish logical stop 0.
        home_result = position.calibrate(
            home_direction=args.home_direction,
            max_home_steps=args.home_max_steps,
        )
        # Establish a known gate state after boot calibration before the first item.
        gate.close()
        results = []
        cycle = SortingCycle(model, position, gate)
        for image in args.images:
            result = cycle.run(image)
            results.append(
                {
                    "category": result.prediction.category,
                    "confidence": result.prediction.confidence,
                    "image": str(result.image_path),
                    "position": result.position_plan.__dict__,
                    "timings_ms": result.timings_ms,
                }
            )
        print(
            json.dumps(
                {
                    "calibration": home_result.__dict__,
                    "cycles": results,
                    "safe_stop": True,
                },
                sort_keys=True,
            )
        )
        return 0
    except HomingError as exc:
        print(json.dumps({"error": str(exc), "safe_stop": True}, sort_keys=True))
        return 2
    finally:
        servo.stop()
        home_sensor.close()
        stepper.close()


if __name__ == "__main__":
    raise SystemExit(main())
