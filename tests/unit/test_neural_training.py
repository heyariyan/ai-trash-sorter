import tempfile
import unittest
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "training" / "scripts"))

from train_neural import CLASSES, class_weights, stratified_split  # noqa: E402


class NeuralTrainingTests(unittest.TestCase):
    def test_stratified_split_keeps_all_material_classes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            rows = []
            for label in CLASSES:
                for index in range(10):
                    path = Path(directory) / f"{label}-{index}.jpg"
                    path.write_bytes(b"placeholder")
                    rows.append({"path": str(path), "label": label})
            train, validation, test = stratified_split(rows, 0.2, 0.2, 42)

        self.assertEqual({row["label"] for row in train}, set(CLASSES))
        self.assertEqual({row["label"] for row in validation}, set(CLASSES))
        self.assertEqual({row["label"] for row in test}, set(CLASSES))
        self.assertEqual(len(train) + len(validation) + len(test), len(rows))

    def test_class_weights_are_balanced_for_balanced_data(self) -> None:
        rows = [{"path": str(index), "label": label} for label in CLASSES for index in range(2)]
        weights = class_weights(rows)
        self.assertEqual(weights, {0: 1.0, 1: 1.0, 2: 1.0, 3: 1.0})


if __name__ == "__main__":
    unittest.main()
