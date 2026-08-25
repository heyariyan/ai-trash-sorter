"""Run one explicitly bounded timed IR-home search.

The command stops on GPIO23 HIGH, a 90-second default deadline, or the
maximum pulse count. Physical movement requires ``--confirm-movement``.
"""

from __future__ import annotations

import argparse
import json
from time import monotonic

from sensors.ir_home import IRHomeSensor

from .homing import HomingError, home_stepper_for_seconds
from .stepper import LgpioStepper


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--direction", type=int, choices=(0, 1), default=0)
    parser.add_argument("--seconds", type=float, default=90.0)
    parser.add_argument("--max-steps", type=int, default=2000)
    parser.add_argument("--pulse-delay-ms", type=float, default=50.0)
    parser.add_argument("--home-gpio", type=int, default=23)
    parser.add_argument("--confirm-movement", action="store_true")
    args = parser.parse_args()
    if args.seconds <= 0 or args.max_steps <= 0 or args.pulse_delay_ms <= 0:
        raise SystemExit("seconds, max-steps, and pulse-delay-ms must be positive")
    if not args.confirm_movement:
        raise SystemExit("refusing physical homing; pass --confirm-movement after preflight")

    stepper = LgpioStepper(pulse_delay_seconds=args.pulse_delay_ms / 1000)
    sensor = IRHomeSensor(gpio=args.home_gpio, home_level=1)
    started = monotonic()
    try:
        stepper.start()
        sensor.start()
        result = home_stepper_for_seconds(
            stepper,
            sensor,
            direction=args.direction,
            seconds=args.seconds,
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
