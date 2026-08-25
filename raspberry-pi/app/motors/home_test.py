"""Run one explicitly bounded IR-home verification.

The command is deliberately locked: physical movement requires the explicit
``--confirm-movement`` flag.  If GPIO23 is already HIGH, no movement occurs.
"""

from __future__ import annotations

import argparse
import json
from time import monotonic

from sensors.ir_home import IRHomeSensor

from .homing import HomingError, home_stepper
from .stepper import LgpioStepper


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--direction", type=int, choices=(0, 1), default=0)
    parser.add_argument("--max-steps", type=int, default=400)
    parser.add_argument("--pulse-delay-ms", type=float, default=20.0)
    parser.add_argument("--home-gpio", type=int, default=23)
    parser.add_argument("--confirm-movement", action="store_true")
    args = parser.parse_args()
    if args.max_steps <= 0 or args.pulse_delay_ms <= 0:
        raise SystemExit("max-steps and pulse-delay-ms must be positive")
    if not args.confirm_movement:
        raise SystemExit("refusing physical homing; pass --confirm-movement after preflight")

    stepper = LgpioStepper(pulse_delay_seconds=args.pulse_delay_ms / 1000)
    sensor = IRHomeSensor(gpio=args.home_gpio, home_level=1)
    started = monotonic()
    try:
        stepper.start()
        sensor.start()
        result = home_stepper(
            stepper,
            sensor,
            direction=args.direction,
            max_steps=args.max_steps,
        )
        print(
            json.dumps(
                {
                    "already_home": result.already_home,
                    "direction": args.direction,
                    "elapsed_ms": round((monotonic() - started) * 1000, 3),
                    "home_gpio": args.home_gpio,
                    "reached_home": result.reached_home,
                    "safe_off": True,
                    "steps_taken": result.steps_taken,
                },
                sort_keys=True,
            )
        )
        return 0
    except HomingError as exc:
        print(json.dumps({"error": str(exc), "safe_off": True}, sort_keys=True))
        return 2
    finally:
        sensor.close()
        stepper.close()


if __name__ == "__main__":
    raise SystemExit(main())
