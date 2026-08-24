"""Capture one image without starting the sorter or any actuator."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .camera import MockCamera, Picamera2Camera


def _simulation_enabled() -> bool:
    return os.environ.get("AI_TRASH_SORTER_SIMULATION", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture one image in camera-only mode")
    parser.add_argument("--output", type=Path, required=True, help="destination image path")
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--simulation", action="store_true", help="use MockCamera")
    args = parser.parse_args()

    simulation = args.simulation or _simulation_enabled()
    camera = (
        MockCamera(width=args.width, height=args.height)
        if simulation
        else Picamera2Camera(width=args.width, height=args.height)
    )
    camera.start()
    try:
        result = camera.capture(args.output)
    finally:
        camera.stop()

    print(
        json.dumps(
            {
                "path": str(result.path),
                "captured_at": result.captured_at,
                "width": result.width,
                "height": result.height,
                "capture_time_ms": result.capture_time_ms,
                "simulated": result.simulated,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
