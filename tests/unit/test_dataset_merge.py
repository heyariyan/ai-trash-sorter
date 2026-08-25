import sys
import unittest
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "training" / "dataset"))

from merge_taco_kaggle import (  # noqa: E402
    process_kaggle_images,
    process_taco_images,
    remap_taco_category,
)


class TacoMappingTests(unittest.TestCase):
    def test_material_variants_follow_project_policy(self) -> None:
        self.assertEqual(remap_taco_category("plastic bottle cap"), "PLASTIC")
        self.assertEqual(remap_taco_category("other_plastic_wrapper"), "PLASTIC")
        self.assertEqual(remap_taco_category("metal_bottle_cap"), "METAL")
        self.assertEqual(remap_taco_category("drink_can"), "METAL")
        self.assertEqual(remap_taco_category("normal_paper"), "BIODEGRADABLE")
        self.assertEqual(remap_taco_category("corrugated_carton"), "BIODEGRADABLE")
        self.assertEqual(remap_taco_category("glass_bottle"), "OTHER")
        self.assertEqual(remap_taco_category("unlabeled_litter"), "OTHER")

    def test_mixed_taco_image_is_conservatively_other(self) -> None:
        import json

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image = root / "data" / "mixed.jpg"
            image.parent.mkdir(parents=True)
            image.write_bytes(b"image")
            (root / "annotations.json").write_text(
                json.dumps(
                    {
                        "images": [{"id": 1, "file_name": "data/mixed.jpg"}],
                        "categories": [
                            {"id": 1, "name": "Plastic bottle"},
                            {"id": 2, "name": "Metal can"},
                        ],
                        "annotations": [
                            {"image_id": 1, "category_id": 1},
                            {"image_id": 1, "category_id": 2},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            output = root / "manifest.jsonl"
            counts = process_taco_images(root, output, max_per_class=10)
            row = json.loads(output.read_text(encoding="utf-8").splitlines()[0])

        self.assertEqual(counts, {"OTHER": 1})
        self.assertEqual(row["label"], "OTHER")
        self.assertEqual(row["source_categories"], ["Metal can", "Plastic bottle"])

    def test_kaggle_respects_existing_class_cap(self) -> None:
        import json

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            class_dir = root / "Plastic"
            class_dir.mkdir(parents=True)
            (class_dir / "bottle.jpg").write_bytes(b"image")
            output = root / "manifest.jsonl"
            counts = process_kaggle_images(
                root, output, max_per_class=1, initial_counts={"PLASTIC": 1}
            )
            content = output.read_text(encoding="utf-8")

        self.assertEqual(counts, {})
        self.assertEqual(content, "")
