"""Download a bounded, reproducible TACO image subset on the dev machine.

TACO stores image URLs in its COCO annotations. This script keeps the
annotations for selected images and downloads the resized Flickr image for
each selected sample. It never runs on the Raspberry Pi.
"""

from __future__ import annotations

import argparse
import json
import random
import urllib.request
from collections import defaultdict
from io import BytesIO
from pathlib import Path

from PIL import Image

from merge_taco_kaggle import remap_taco_category


def _image_label(image_id: int, annotations: list[dict], categories: dict[int, str]) -> str:
    names = {categories.get(row["category_id"], "Unlabeled litter") for row in annotations if row["image_id"] == image_id}
    mapped = {remap_taco_category(name) for name in names}
    return mapped.pop() if len(mapped) == 1 else "OTHER"


def download_subset(source: Path, output: Path, max_per_class: int, seed: int) -> dict[str, int]:
    if max_per_class <= 0:
        raise ValueError("max_per_class must be positive")
    dataset = json.loads(source.read_text(encoding="utf-8"))
    categories = {int(row["id"]): str(row["name"]) for row in dataset.get("categories", [])}
    annotations_by_image: dict[int, list[dict]] = defaultdict(list)
    for row in dataset.get("annotations", []):
        annotations_by_image[int(row["image_id"])].append(row)

    candidates: dict[str, list[dict]] = defaultdict(list)
    for image in dataset.get("images", []):
        image_id = int(image["id"])
        if image_id in annotations_by_image:
            candidates[_image_label(image_id, annotations_by_image[image_id], categories)].append(image)
    rng = random.Random(seed)
    selected: list[dict] = []
    counts: dict[str, int] = defaultdict(int)
    for label, images in sorted(candidates.items()):
        rng.shuffle(images)
        selected.extend(images[:max_per_class])
        counts[label] = min(len(images), max_per_class)

    selected_ids = {int(image["id"]) for image in selected}
    output.mkdir(parents=True, exist_ok=True)
    downloaded: list[dict] = []
    failed: list[dict[str, str]] = []
    for index, image in enumerate(selected, 1):
        relative = Path(str(image["file_name"]))
        destination = output / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.is_file():
            url = str(image.get("flickr_640_url") or image.get("flickr_url"))
            request = urllib.request.Request(url, headers={"User-Agent": "ai-trash-sorter-dataset/1"})
            try:
                with urllib.request.urlopen(request, timeout=15) as response:
                    payload = response.read()
                with Image.open(BytesIO(payload)) as decoded:
                    decoded.convert("RGB").save(destination, format="JPEG", quality=92)
            except Exception as exc:
                failed.append({"file_name": str(relative), "error": str(exc)})
                continue
        downloaded.append(image)
        if index % 25 == 0 or index == len(selected):
            print(f"TACO download: {index}/{len(selected)}")

    subset = {
        "info": dataset.get("info", {}),
        "licenses": dataset.get("licenses", []),
        "images": downloaded,
        "annotations": [row for row in dataset.get("annotations", []) if int(row["image_id"]) in selected_ids],
        "categories": dataset.get("categories", []),
    }
    (output / "annotations.json").write_text(json.dumps(subset, indent=2), encoding="utf-8")
    (output / "download_failures.json").write_text(json.dumps(failed, indent=2), encoding="utf-8")
    actual_counts: dict[str, int] = defaultdict(int)
    for image in downloaded:
        actual_counts[_image_label(int(image["id"]), annotations_by_image[int(image["id"])], categories)] += 1
    return dict(actual_counts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-per-class", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    counts = download_subset(args.annotations, args.output, args.max_per_class, args.seed)
    print(json.dumps({"output": str(args.output), "counts": counts}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
