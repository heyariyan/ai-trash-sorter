import json
import tempfile
import unittest
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "training" / "dataset"))

from remap_labels import build_manifest  # noqa: E402


class LabelRemapTests(unittest.TestCase):
    def test_maps_source_folders_to_project_classes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "dataset"
            (root / "Train" / "Food Organics").mkdir(parents=True)
            (root / "Train" / "Plastic").mkdir(parents=True)
            (root / "Train" / "Glass").mkdir(parents=True)
            for name in ("food.jpg", "bottle.jpg", "jar.jpg"):
                parent = "Food Organics" if name == "food.jpg" else "Plastic" if name == "bottle.jpg" else "Glass"
                (root / "Train" / parent / name).write_bytes(b"test")
            output = Path(directory) / "manifest.jsonl"
            counts = build_manifest(root, output)
            rows = [json.loads(line) for line in output.read_text().splitlines()]

        self.assertEqual(counts, {"BIODEGRADABLE": 1, "OTHER": 1, "PLASTIC": 1})
        self.assertEqual({row["label"] for row in rows}, {"BIODEGRADABLE", "OTHER", "PLASTIC"})
