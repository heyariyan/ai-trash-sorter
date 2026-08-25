"""Run one explicitly bounded DRV8825 movement test."""

from __future__ import annotations

import argparse
import json
from time import monotonic

from .stepper import LgpioStepper


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=int, default=10)
    parser.add_argument("--direction", type=int, choices=(0, 1), default=0)
    parser.add_argument("--pulse-delay-ms", type=float, default=5.0)
    args = parser.parse_args()
    if args.steps <= 0 or args.pulse_delay_ms <= 0:
        raise SystemExit("steps and pulse-delay-ms must be positive")

    stepper = LgpioStepper(pulse_delay_seconds=args.pulse_delay_ms / 1000)
    started = monotonic()
    stepper.start()
    try:
        stepper.move_steps(args.steps, args.direction)
    finally:
        stepper.close()
    print(
        json.dumps(
            {
                "steps": args.steps,
                "direction": args.direction,
                "pulse_delay_ms": args.pulse_delay_ms,
                "elapsed_ms": round((monotonic() - started) * 1000, 3),
                "safe_off": True,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
