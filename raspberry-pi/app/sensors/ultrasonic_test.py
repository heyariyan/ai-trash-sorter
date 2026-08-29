"""Diagnostic and test CLI for U1 (intake trigger) and U3 (bin fill) ultrasonic sensors."""

from __future__ import annotations

import argparse
from time import sleep

from sensors.ultrasonic import LgpioUltrasonicSensor, MockUltrasonicSensor


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--u1-trig", type=int, default=4, help="U1 intake TRIG GPIO (default: 4)")
    parser.add_argument("--u1-echo", type=int, default=5, help="U1 intake ECHO GPIO (default: 5)")
    parser.add_argument("--u3-trig", type=int, default=27, help="U3 bin status TRIG GPIO (default: 27)")
    parser.add_argument("--u3-echo", type=int, default=13, help="U3 bin status ECHO GPIO (default: 13)")
    parser.add_argument("--presence-threshold-cm", type=float, default=7.0)
    parser.add_argument("--samples", type=int, default=10, help="Number of samples (0 for infinite loop)")
    parser.add_argument("--interval-seconds", type=float, default=0.5)
    parser.add_argument("--simulation", action="store_true")
    args = parser.parse_args()

    if args.simulation:
        print("Running in SIMULATION mode with mock ultrasonic sensors.")
        u1 = MockUltrasonicSensor([15.0, 12.0, 6.2, 5.8, 18.0, 6.5, 20.0, 4.9, 14.0, 25.0])
        u3 = MockUltrasonicSensor([22.0, 22.1, 18.5, 18.4, 18.2, 14.0, 14.1, 9.8, 9.7, 24.0])
    else:
        print(f"Initializing U1 on TRIG={args.u1_trig}, ECHO={args.u1_echo}...")
        u1 = LgpioUltrasonicSensor(args.u1_trig, args.u1_echo)
        u1.start()
        print(f"Initializing U3 on TRIG={args.u3_trig}, ECHO={args.u3_echo}...")
        u3 = LgpioUltrasonicSensor(args.u3_trig, args.u3_echo)
        u3.start()

    print(f"\nMonitoring Sensors (Presence Threshold: <= {args.presence_threshold_cm:.1f} cm)")
    print("-" * 65)
    print(f"{'Sample':<8} | {'U1 Intake (cm)':<18} | {'U3 Bin (cm)':<18} | {'U1 Status'}")
    print("-" * 65)

    sample_count = 0
    try:
        while args.samples == 0 or sample_count < args.samples:
            sample_count += 1
            u1_dist = u1.read_distance_cm()
            u3_dist = u3.read_distance_cm()

            u1_str = f"{u1_dist:.1f}" if u1_dist is not None else "TIMEOUT"
            u3_str = f"{u3_dist:.1f}" if u3_dist is not None else "TIMEOUT"

            if u1_dist is not None and u1_dist <= args.presence_threshold_cm:
                status = f"** TRIGGER (<= {args.presence_threshold_cm:.1f}cm) **"
            elif u1_dist is not None:
                status = "CLEAR"
            else:
                status = "NO ECHO"

            print(f"{sample_count:<8} | {u1_str:<18} | {u3_str:<18} | {status}")
            sleep(args.interval_seconds)

        print("-" * 65)
        print("Ultrasonic test completed successfully.")
        return 0
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
        return 0
    finally:
        for sensor in (u1, u3):
            close = getattr(sensor, "close", None)
            if callable(close):
                close()


if __name__ == "__main__":
    raise SystemExit(main())
