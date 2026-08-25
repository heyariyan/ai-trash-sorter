"""Run bounded continuous DRV8825 motion; never run without confirmation."""

from __future__ import annotations

import argparse
import json
from time import monotonic

from .stepper import LgpioStepper


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=float, default=10.0)
    parser.add_argument("--direction", type=int, choices=(0, 1), default=0)
    parser.add_argument("--pulse-delay-ms", type=float, default=5.0)
    parser.add_argument(
        "--confirm-movement",
        action="store_true",
        help="required acknowledgement that the motor will move continuously",
    )
    args = parser.parse_args()
    if not args.confirm_movement:
        raise SystemExit("refusing to move: add --confirm-movement after checking the workspace")
    if args.seconds <= 0 or args.pulse_delay_ms <= 0:
        raise SystemExit("seconds and pulse-delay-ms must be positive")

    stepper = LgpioStepper(pulse_delay_seconds=args.pulse_delay_ms / 1000)
    started = monotonic()
    pulses = 0
    stepper.start()
    try:
        pulses = stepper.move_for_seconds(args.seconds, args.direction)
    finally:
        stepper.close()
    print(
        json.dumps(
            {
                "requested_seconds": args.seconds,
                "direction": args.direction,
                "pulse_delay_ms": args.pulse_delay_ms,
                "pulses": pulses,
                "elapsed_ms": round((monotonic() - started) * 1000, 3),
                "safe_off": True,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
