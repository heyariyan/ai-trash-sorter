"""Run one bounded MG995 gate open/close test after safety confirmation."""

from __future__ import annotations

import argparse
import json

from .servo import GateConfig, LgpioServo, ServoGate


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--signal-gpio", type=int, default=18)
    parser.add_argument("--closed-angle", type=float, default=0.0)
    parser.add_argument("--open-angle", type=float, default=90.0)
    parser.add_argument("--settle-seconds", type=float, default=0.5)
    parser.add_argument("--confirm-movement", action="store_true")
    args = parser.parse_args()
    if not args.confirm_movement:
        raise SystemExit("refusing servo movement; pass --confirm-movement after preflight")

    servo = LgpioServo(signal_gpio=args.signal_gpio)
    gate = ServoGate(
        servo,
        GateConfig(
            closed_angle=args.closed_angle,
            open_angle=args.open_angle,
            settle_seconds=args.settle_seconds,
        ),
    )
    try:
        servo.start()
        gate.close()
        gate.open()
        gate.close()
        print(json.dumps({"closed": not gate.is_open, "safe_stop": True}, sort_keys=True))
        return 0
    finally:
        servo.stop()


if __name__ == "__main__":
    raise SystemExit(main())
