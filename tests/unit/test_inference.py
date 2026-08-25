import json
import tempfile
import unittest
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "raspberry-pi" / "app"))

from PIL import Image  # noqa: E402
from ai import TFLiteModel  # noqa: E402


class FakeInterpreter:
    def __init__(self, **_: object) -> None:
        import numpy as np

        self.tensor = None
        self.output = np.array([[0, 0, 255, 0]], dtype=np.uint8)

    def allocate_tensors(self) -> None:
        return None

    def get_input_details(self) -> list[dict[str, object]]:
        import numpy as np

        return [{"index": 3, "shape": [1, 4, 4, 3], "dtype": np.dtype(np.uint8), "quantization": (1 / 255, 0)}]

    def get_output_details(self) -> list[dict[str, object]]:
        import numpy as np

        return [{"index": 7, "dtype": np.dtype(np.uint8), "quantization": (1 / 255, 0)}]

    def set_tensor(self, _: int, tensor: object) -> None:
        self.tensor = tensor

    def invoke(self) -> None:
        return None

    def get_tensor(self, _: int) -> object:
        return self.output


class InferenceTests(unittest.TestCase):
    def test_quantized_neural_prediction_contains_required_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            model_path = root / "model.tflite"
            model_path.write_bytes(b"fake")
            metadata_path = root / "model.json"
            metadata_path.write_text(
                json.dumps(
                    {
                        "format": "tflite_classifier_v1",
                        "model_version": "mobilenet-test-v1",
                        "classes": ["BIODEGRADABLE", "PLASTIC", "METAL", "OTHER"],
                    }
                ),
                encoding="utf-8",
            )
            image_path = root / "image.jpg"
            Image.new("RGB", (8, 8), (255, 0, 0)).save(image_path)
            prediction = TFLiteModel(model_path, metadata_path, FakeInterpreter).predict(image_path)

        self.assertEqual(prediction.category, "METAL")
        self.assertEqual(prediction.model_version, "mobilenet-test-v1")
        self.assertEqual(prediction.confidence, 1.0)
        self.assertGreaterEqual(prediction.inference_time_ms, 0)
        self.assertTrue(prediction.timestamp)


if __name__ == "__main__":
    unittest.main()
