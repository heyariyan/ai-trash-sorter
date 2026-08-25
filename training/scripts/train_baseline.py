"""Removed RGB baseline entry point.

M3 now requires the neural MobileNetV2/TFLite pipeline. Use
``training/scripts/train_neural.py``; this file remains only to give an
actionable error to old automation that still calls the former command.
"""

from __future__ import annotations

def main() -> int:
    raise SystemExit(
        "The RGB-centroid baseline is retired. Run training/scripts/train_neural.py "
        "with a merged TACO+Kaggle manifest instead."
    )


if __name__ == "__main__":
    raise SystemExit(main())
