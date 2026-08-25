"""Create a four-class JSONL manifest without copying raw dataset images."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


LABEL_MAP = {
    "food organics": "BIODEGRADABLE",
    "vegetation": "BIODEGRADABLE",
    "plastic": "PLASTIC",
    "metal": "METAL",
    "cardboard": "BIODEGRADABLE",
    "glass": "OTHER",
    "paper": "BIODEGRADABLE",
    "textile trash": "OTHER",
    "miscellaneous trash": "OTHER",
}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def _normalise(value: str) -> str:
    value = value.replace("_", " ").replace("-", " ")
    value = re.sub(r"^\s*\d+\s+", "", value)
    return re.sub(r"\s+", " ", value.strip().lower())


def source_label_for(path: Path, root: Path) -> str | None:
    """Find the nearest mapped class directory above an image."""

    root = root.resolve()
    for parent in (path.resolve().parent, *path.resolve().parents):
        if parent == root.parent:
            break
        mapped = LABEL_MAP.get(_normalise(parent.name))
        if mapped is not None:
            return parent.name
        if parent == root:
            break
    return None


def build_manifest(root: Path, output: Path) -> dict[str, int]:
    root = root.resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"dataset root does not exist: {root}")

    counts: dict[str, int] = {}
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as manifest:
        for image in sorted(root.rglob("*")):
            if not image.is_file() or image.suffix.lower() not in IMAGE_EXTENSIONS:
                continue
            source_label = source_label_for(image, root)
            if source_label is None:
                continue
            target_label = LABEL_MAP[_normalise(source_label)]
            row = {
                "path": str(image),
                "source_label": source_label,
                "label": target_label,
            }
            manifest.write(json.dumps(row, sort_keys=True) + "\n")
            counts[target_label] = counts.get(target_label, 0) + 1
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    counts = build_manifest(args.root, args.output)
    print(json.dumps({"manifest": str(args.output), "counts": counts}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
