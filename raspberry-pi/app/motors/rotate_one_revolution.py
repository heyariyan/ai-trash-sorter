"""Rotate the DRV8825/NEMA17 one revolution without homing or other hardware."""

from __future__ import annotations

import argparse
import json
from time import monotonic

from .stepper import LgpioStepper


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--steps-per-revolution",
        type=int,
        default=200,
        help="full-step pulses for one revolution (200 for a 1.8-degree motor)",
    )
    parser.add_argument("--direction", type=int, choices=(0, 1), default=0)
    parser.add_argument("--pulse-delay-ms", type=float, default=5.0)
    args = parser.parse_args()
    if args.steps_per_revolution <= 0 or args.pulse_delay_ms <= 0:
        raise SystemExit("steps-per-revolution and pulse-delay-ms must be positive")

    stepper = LgpioStepper(pulse_delay_seconds=args.pulse_delay_ms / 1000)
    started = monotonic()
    stepper.start()
    try:
        stepper.move_steps(args.steps_per_revolution, args.direction)
    finally:
        stepper.close()
    print(
        json.dumps(
            {
                "steps": args.steps_per_revolution,
                "direction": args.direction,
                "pulse_delay_ms": args.pulse_delay_ms,
                "safe_off": True,
                "elapsed_ms": round((monotonic() - started) * 1000, 3),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
