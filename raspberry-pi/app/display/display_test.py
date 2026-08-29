"""Interactive and automated test utility for SSD1306 OLED and Console display."""

from __future__ import annotations

import argparse
from time import sleep

from display.display import ConsoleDisplay, MockDisplay, SSD1306I2CDisplay


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--display", choices=("console", "ssd1306", "mock"), default="console")
    parser.add_argument("--simulation", action="store_true")
    parser.add_argument("--delay-seconds", type=float, default=2.0)
    args = parser.parse_args()

    if args.display == "mock" or (args.display == "ssd1306" and args.simulation):
        print("Using Mock / Simulated Display")
        display = MockDisplay()
    elif args.display == "ssd1306":
        print("Initializing physical SSD1306 OLED on I2C GPIO2/GPIO3...")
        display = SSD1306I2CDisplay()
        display.start()
    else:
        display = ConsoleDisplay()

    try:
        print("\n--- Screen 1: Status (Starting / Boot) ---")
        display.show_status("Starting System...")
        sleep(args.delay_seconds)

        print("\n--- Screen 2: Status (Calibrating) ---")
        display.show_status("Calibrating Home...")
        sleep(args.delay_seconds)

        print("\n--- Screen 3: Status (Ready) ---")
        display.show_status("Ready / Standby")
        sleep(args.delay_seconds)

        print("\n--- Screen 4: Prediction (PLASTIC 94.2%) ---")
        display.show_prediction("PLASTIC", 0.942)
        sleep(args.delay_seconds)

        print("\n--- Screen 5: Bin Status (Post-drop measurement) ---")
        display.show_bin_status("PLASTIC", 17.8)
        sleep(args.delay_seconds)

        print("\n--- Screen 6: Feedback Prompt (YES/NO) ---")
        display.show_feedback_prompt("PLASTIC correct?")
        sleep(args.delay_seconds)

        print("\n--- Screen 7: Feedback Selection (Correction menu) ---")
        display.show_feedback_prompt("Select correct bin", "METAL")
        sleep(args.delay_seconds)

        print("\n--- Screen 8: Error Screen ---")
        display.show_error("Homing timeout 1000 steps")
        sleep(args.delay_seconds)

        print("\n--- Return to Ready ---")
        display.show_status("Ready")
        print("\nDisplay test completed successfully.")
        return 0
    finally:
        display.close()


if __name__ == "__main__":
    raise SystemExit(main())
