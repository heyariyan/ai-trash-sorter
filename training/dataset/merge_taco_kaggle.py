"""Merge TACO (full taxonomy) and Kaggle datasets into a unified manifest.

This script:
1. Uses a local TACO checkout (the published taxonomy is larger than 16 categories)
2. Uses existing Kaggle bootstrap data
3. Remaps both to 4 unified classes: BIODEGRADABLE, PLASTIC, METAL, OTHER
4. Creates a combined JSONL manifest suitable for training

TACO taxonomy: https://github.com/pedropro/TACO
Kaggle source: Adithya Challa's Waste Classification
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path


# ============================================================================
# TACO seed taxonomy → 4-class remapping
# ============================================================================
# TACO provides hierarchical categories with segmentation masks in annotations.json.
# The published taxonomy is larger than this seed table; fallback rules below
# cover material variants and unknown classes remain OTHER for review.

TACO_TO_4CLASS = {
    # PLASTIC (TACO IDs: 1-7)
    "Plastic bag": "PLASTIC",
    "Plastic bottle": "PLASTIC",
    "Plastic film": "PLASTIC",
    "Plastic container": "PLASTIC",
    "Plastic straw": "PLASTIC",
    "Plastic cup": "PLASTIC",
    "Plastic utensil": "PLASTIC",
    
    # METAL (TACO IDs: 8-9)
    "Metal can": "METAL",
    "Metal container": "METAL",
    
    # BIODEGRADABLE (TACO IDs: 10-13)
    "Organic waste": "BIODEGRADABLE",
    "Paper": "BIODEGRADABLE",  # Paper degrades, repurposable
    "Cardboard": "BIODEGRADABLE",  # Cardboard degrades, repurposable
    "Food waste": "BIODEGRADABLE",
    
    # OTHER (unsupported, mixed, or unknown material)
    "Textile": "OTHER",
    "Rubber": "OTHER",
    "Glass": "OTHER",  # Not part of current 4-class, but in TACO
    "Uncertainty": "OTHER",  # Low-confidence TACO annotations
}


def _normalise_taco_category(value: str) -> str:
    """Normalize TACO category spelling and separators."""
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", value.lower())).strip()


TACO_TO_4CLASS_NORMALIZED = {
    _normalise_taco_category(source): target for source, target in TACO_TO_4CLASS.items()
}


def remap_taco_category(category: str) -> str:
    """Map known and common TACO taxonomy variants to the four project classes.

    Unknown categories intentionally remain OTHER. The category audit must be
    updated if a future TACO release introduces a material that these rules do
    not cover.
    """
    normalized = _normalise_taco_category(category)
    direct = TACO_TO_4CLASS_NORMALIZED.get(normalized)
    if direct is not None:
        return direct

    # TACO contains variants such as plastic bottle caps, wrappers, and lids.
    if "plastic" in normalized:
        return "PLASTIC"

    # Cover explicit metal variants and common metal-only litter names.
    if any(token in normalized for token in ("metal", "aluminium", "aluminum", "steel")):
        return "METAL"
    if normalized in {"drink can", "pop tab", "foil"}:
        return "METAL"

    # Paper/cardboard/carton items are biodegradable under the project policy.
    if any(token in normalized for token in ("paper", "cardboard", "carton", "food waste", "organic")):
        return "BIODEGRADABLE"

    return "OTHER"

# ============================================================================
# KAGGLE SOURCE-FOLDER TAXONOMY → 4-CLASS REMAPPING
# ============================================================================

KAGGLE_TO_4CLASS = {
    "food organics": "BIODEGRADABLE",
    "vegetation": "BIODEGRADABLE",
    "plastic": "PLASTIC",
    "metal": "METAL",
    "cardboard": "BIODEGRADABLE",  # Repurposable
    "glass": "OTHER",
    "paper": "BIODEGRADABLE",  # Repurposable
    "textile trash": "OTHER",
    "miscellaneous trash": "OTHER",
}


# ============================================================================
# TACO DATASET PARSING
# ============================================================================

def load_taco_annotations(taco_root: Path) -> dict[str, list[dict]]:
    """
    Load TACO annotations.json and extract image→class mappings.
    
    TACO structure:
    ```
    taco_root/
      annotations.json  (contains image metadata and category info)
      data/
        train/  (images)
        test/   (images)
    ```
    
    Returns: {image_id: [{'image': path, 'category': class_name, ...}, ...]}
    """
    annotations_file = taco_root / "annotations.json"
    if not annotations_file.exists():
        raise FileNotFoundError(
            f"TACO annotations.json not found at {annotations_file}. "
            "Download from: https://github.com/pedropro/TACO"
        )
    
    with annotations_file.open(encoding="utf-8") as f:
        taco_data = json.load(f)
    
    # TACO structure: images, annotations, categories
    images = {img["id"]: img for img in taco_data.get("images", [])}
    categories = {cat["id"]: cat["name"] for cat in taco_data.get("categories", [])}
    annotations = taco_data.get("annotations", [])
    
    # Map each image to its primary category (most frequent annotation)
    image_categories: dict[str, list[dict]] = defaultdict(list)
    
    for ann in annotations:
        img_id = ann["image_id"]
        if img_id not in images:
            continue
        
        cat_id = ann["category_id"]
        cat_name = categories.get(cat_id, "unknown")
        img_path = images[img_id]["file_name"]
        
        # Resolve full path
        taco_images_path = taco_root / img_path
        if taco_images_path.is_file():
            image_categories[img_id].append({
                "path": str(taco_images_path),
                "category": cat_name,
                "source": "taco",
            })
    
    return image_categories


def process_taco_images(
    taco_root: Path,
    output: Path,
    max_per_class: int = 250,
) -> dict[str, int]:
    """
    Process TACO dataset and write to JSONL manifest.
    
    Returns: count by 4-class label
    """
    image_categories = load_taco_annotations(taco_root)
    
    counts: dict[str, int] = defaultdict(int)
    written = 0
    skipped = 0
    
    output.parent.mkdir(parents=True, exist_ok=True)
    
    with output.open("w", encoding="utf-8") as manifest:
        for img_id, annotations in sorted(image_categories.items()):
            if not annotations:
                continue
            
            categories_for_image = sorted({ann["category"] for ann in annotations})
            mapped_classes = {remap_taco_category(category) for category in categories_for_image}
            # Image-level classification cannot safely choose one material when
            # annotations disagree; retain it as OTHER and preserve categories.
            target_class = mapped_classes.pop() if len(mapped_classes) == 1 else "OTHER"
            taco_class = categories_for_image[0]
            img_path = annotations[0]["path"]
            
            # Enforce per-class limit
            if counts[target_class] >= max_per_class:
                skipped += 1
                continue
            
            # Verify file exists
            if not Path(img_path).is_file():
                skipped += 1
                continue
            
            row = {
                "path": img_path,
                "source_label": taco_class,
                "source_categories": categories_for_image,
                "label": target_class,
                "source": "taco",
            }
            manifest.write(json.dumps(row, sort_keys=True) + "\n")
            counts[target_class] += 1
            written += 1
    
    print(f"TACO: Processed {written} images (skipped {skipped})")
    return dict(counts)


# ============================================================================
# KAGGLE DATASET PROCESSING (reuse existing logic)
# ============================================================================

def _normalise(value: str) -> str:
    """Normalize directory names to class keys."""
    value = value.replace("_", " ").replace("-", " ")
    value = re.sub(r"^\s*\d+\s+", "", value)
    return re.sub(r"\s+", " ", value.strip().lower())


def source_label_for_kaggle(path: Path, root: Path) -> str | None:
    """Find the nearest mapped class directory above a Kaggle image."""
    root = root.resolve()
    for parent in (path.resolve().parent, *path.resolve().parents):
        if parent == root.parent:
            break
        mapped = KAGGLE_TO_4CLASS.get(_normalise(parent.name))
        if mapped is not None:
            return parent.name
        if parent == root:
            break
    return None


def process_kaggle_images(
    kaggle_root: Path,
    output: Path,
    max_per_class: int = 250,
    initial_counts: dict[str, int] | None = None,
) -> dict[str, int]:
    """
    Process Kaggle dataset and append to existing manifest.
    
    Returns: count by 4-class label
    """
    kaggle_root = kaggle_root.resolve()
    if not kaggle_root.is_dir():
        raise FileNotFoundError(f"Kaggle dataset root does not exist: {kaggle_root}")
    
    IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    counts: dict[str, int] = defaultdict(int)
    available = defaultdict(int, initial_counts or {})
    written = 0
    skipped = 0
    
    # Append to existing manifest
    mode = "a" if output.exists() else "w"
    output.parent.mkdir(parents=True, exist_ok=True)
    
    with output.open(mode, encoding="utf-8") as manifest:
        for image in sorted(kaggle_root.rglob("*")):
            if not image.is_file() or image.suffix.lower() not in IMAGE_EXTENSIONS:
                continue
            
            source_label = source_label_for_kaggle(image, kaggle_root)
            if source_label is None:
                skipped += 1
                continue
            
            target_label = KAGGLE_TO_4CLASS[_normalise(source_label)]
            
            # Enforce per-class limit
            if available[target_label] >= max_per_class:
                skipped += 1
                continue
            
            row = {
                "path": str(image),
                "source_label": source_label,
                "label": target_label,
                "source": "kaggle",
            }
            manifest.write(json.dumps(row, sort_keys=True) + "\n")
            counts[target_label] += 1
            available[target_label] += 1
            written += 1
    
    print(f"Kaggle: Processed {written} images (skipped {skipped})")
    return dict(counts)


# ============================================================================
# MAIN: MERGE BOTH DATASETS
# ============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--taco-root",
        type=Path,
        help="Path to TACO dataset root (contains annotations.json and data/)",
    )
    parser.add_argument(
        "--kaggle-root",
        type=Path,
        help="Path to Kaggle waste classification dataset root",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Output JSONL manifest path",
    )
    parser.add_argument(
        "--max-per-class",
        type=int,
        default=250,
        help="Maximum images per 4-class label (default: 250)",
    )
    parser.add_argument(
        "--taco-only",
        action="store_true",
        help="Process only TACO (skip Kaggle)",
    )
    parser.add_argument(
        "--kaggle-only",
        action="store_true",
        help="Process only Kaggle (skip TACO)",
    )
    
    args = parser.parse_args()

    # A merge is reproducible: never silently append to a stale prior manifest.
    if args.output.exists():
        args.output.unlink()
    
    all_counts: dict[str, int] = defaultdict(int)
    
    # Process TACO
    if args.taco_root and not args.kaggle_only:
        print(f"\n📦 Processing TACO dataset from {args.taco_root}...")
        taco_counts = process_taco_images(args.taco_root, args.output, args.max_per_class)
        for label, count in taco_counts.items():
            all_counts[label] += count
    
    # Process Kaggle (append to TACO)
    if args.kaggle_root and not args.taco_only:
        print(f"\n📦 Processing Kaggle dataset from {args.kaggle_root}...")
        kaggle_counts = process_kaggle_images(
            args.kaggle_root, args.output, args.max_per_class, dict(all_counts)
        )
        for label, count in kaggle_counts.items():
            all_counts[label] += count
    
    # Summary
    print("\n" + "="*60)
    print("📊 MERGED DATASET SUMMARY")
    print("="*60)
    total = sum(all_counts.values())
    for label in sorted(all_counts.keys()):
        count = all_counts[label]
        pct = (count / total * 100) if total else 0
        print(f"  {label:20} {count:5} images ({pct:5.1f}%)")
    print(f"  {'TOTAL':20} {total:5} images")
    print("="*60)
    print(f"\n✅ Manifest written to: {args.output}")
    print(f"   Next: Use this manifest for training/splits\n")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
