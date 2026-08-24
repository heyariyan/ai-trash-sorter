"""Train a tiny RGB-centroid baseline from a JSONL image manifest.

This is a transparent M3 baseline, not the final quantized neural model. It
uses only Pillow plus the Python standard library and exports a JSON model so
the same feature/scoring code can run on the Pi.
"""

from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image


def extract_feature(path: Path, image_size: int) -> list[float]:
    with Image.open(path) as image:
        image = image.convert("RGB").resize((image_size, image_size), Image.Resampling.BILINEAR)
        pixels = image.load()
        return [
            channel / 255.0
            for y in range(image_size)
            for x in range(image_size)
            for channel in pixels[x, y]
        ]


def mean_vector(vectors: list[list[float]]) -> list[float]:
    if not vectors:
        raise ValueError("cannot average an empty vector set")
    width = len(vectors[0])
    return [sum(vector[index] for vector in vectors) / len(vectors) for index in range(width)]


def distance(left: list[float], right: list[float]) -> float:
    return sum((a - b) ** 2 for a, b in zip(left, right)) ** 0.5


def predict(feature: list[float], centroids: dict[str, list[float]]) -> str:
    return min(centroids, key=lambda label: distance(feature, centroids[label]))


def load_rows(manifest: Path, max_per_class: int) -> dict[str, list[dict[str, str]]]:
    rows_by_class: dict[str, list[dict[str, str]]] = defaultdict(list)
    with manifest.open(encoding="utf-8") as source:
        for line in source:
            row = json.loads(line)
            if Path(row["path"]).is_file() and len(rows_by_class[row["label"]]) < max_per_class:
                rows_by_class[row["label"]].append(row)
    if len(rows_by_class) < 2:
        raise ValueError("manifest must contain at least two target classes with readable images")
    return rows_by_class


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--image-size", type=int, default=8)
    parser.add_argument("--max-per-class", type=int, default=250)
    parser.add_argument("--test-ratio", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--model-version", default="baseline-rgb-centroid-v0")
    args = parser.parse_args()
    if args.image_size <= 0 or args.max_per_class <= 0 or not 0 < args.test_ratio < 1:
        raise ValueError("image-size/max-per-class must be positive and test-ratio must be between 0 and 1")

    rng = random.Random(args.seed)
    rows_by_class = load_rows(args.manifest, args.max_per_class)
    train_rows: list[dict[str, str]] = []
    test_rows: list[dict[str, str]] = []
    for rows in rows_by_class.values():
        rng.shuffle(rows)
        test_count = max(1, int(len(rows) * args.test_ratio)) if len(rows) > 1 else 0
        test_rows.extend(rows[:test_count])
        train_rows.extend(rows[test_count:] or rows[:1])

    train_features: dict[str, list[list[float]]] = defaultdict(list)
    for row in train_rows:
        train_features[row["label"]].append(extract_feature(Path(row["path"]), args.image_size))
    centroids = {label: mean_vector(vectors) for label, vectors in train_features.items()}

    correct = 0
    confusion: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in test_rows:
        actual = row["label"]
        predicted = predict(extract_feature(Path(row["path"]), args.image_size), centroids)
        confusion[actual][predicted] += 1
        correct += int(actual == predicted)
    accuracy = correct / len(test_rows) if test_rows else 0.0

    model = {
        "format": "rgb_centroid_v1",
        "model_version": args.model_version,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "classes": sorted(centroids),
        "image_size": args.image_size,
        "quantization": "none — transparent float baseline",
        "deployment_status": "not_deployed",
        "dataset": {"manifest": str(args.manifest), "max_per_class": args.max_per_class},
        "metrics": {
            "accuracy": accuracy,
            "test_samples": len(test_rows),
            "train_samples": len(train_rows),
            "confusion": confusion,
        },
        "centroids": centroids,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(model, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"model": str(args.output), "accuracy": accuracy, "test_samples": len(test_rows)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
