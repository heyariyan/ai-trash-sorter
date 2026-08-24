"""Run one offline prediction and print a human-readable result."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .inference import RgbCentroidModel


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--image", type=Path, required=True)
    args = parser.parse_args()
    prediction = RgbCentroidModel(args.model).predict(args.image)
    print(f"{prediction.category} — {prediction.confidence * 100:.2f}%")
    print(json.dumps(asdict(prediction), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
