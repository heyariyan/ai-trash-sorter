import json
import tempfile
import unittest
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "raspberry-pi" / "app"))

from PIL import Image  # noqa: E402
from ai import RgbCentroidModel  # noqa: E402


class InferenceTests(unittest.TestCase):
    def test_prediction_contains_required_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            model_path = root / "model.json"
            image_path = root / "image.jpg"
            model = {
                "format": "rgb_centroid_v1",
                "model_version": "test-v0",
                "image_size": 2,
                "centroids": {
                    "PLASTIC": [1.0, 0.0, 0.0] * 4,
                    "METAL": [0.0, 0.0, 1.0] * 4,
                },
            }
            model_path.write_text(json.dumps(model), encoding="utf-8")
            Image.new("RGB", (2, 2), (255, 0, 0)).save(image_path)
            prediction = RgbCentroidModel(model_path).predict(image_path)

        self.assertEqual(prediction.category, "PLASTIC")
        self.assertEqual(prediction.model_version, "test-v0")
        self.assertGreaterEqual(prediction.confidence, 0.5)
        self.assertGreaterEqual(prediction.inference_time_ms, 0)
        self.assertTrue(prediction.timestamp)
