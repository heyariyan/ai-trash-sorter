"""Offline TensorFlow Lite inference for the Raspberry Pi runtime.

The Pi receives a small, quantized neural model plus a JSON sidecar containing
class names and model metadata. This module deliberately has no GPIO, camera,
network, or database dependencies.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from math import exp, isfinite
from pathlib import Path
from time import monotonic
from typing import Any, Callable

from PIL import Image


class InferenceError(RuntimeError):
    """Raised when a model or image cannot be used for inference."""


@dataclass(frozen=True)
class Prediction:
    category: str
    confidence: float
    model_version: str
    inference_time_ms: float
    timestamp: str


def _load_interpreter_factory() -> Callable[..., Any]:
    """Load a supported Lite runtime, with TensorFlow as a dev fallback."""
    try:
        from tflite_runtime.interpreter import Interpreter

        return Interpreter
    except ImportError:
        try:
            from ai_edge_litert.interpreter import Interpreter

            return Interpreter
        except ImportError as exc:
            try:
                from tensorflow.lite import Interpreter

                return Interpreter
            except ImportError:
                raise InferenceError(
                    "Lite runtime is unavailable; install tflite-runtime or "
                    "ai-edge-litert on the Pi, or tensorflow on the development machine"
                ) from exc


class TFLiteModel:
    """Load and run a quantized image classifier exported by train_neural.py."""

    def __init__(
        self,
        model_path: Path,
        metadata_path: Path | None = None,
        interpreter_factory: Callable[..., Any] | None = None,
    ) -> None:
        self.model_path = Path(model_path)
        self.metadata_path = metadata_path or self.model_path.with_suffix(".json")
        try:
            self._metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise InferenceError(f"unable to load model metadata: {self.metadata_path}") from exc
        if self._metadata.get("format") != "tflite_classifier_v1":
            raise InferenceError("unsupported model metadata format")
        self.model_version = str(self._metadata.get("model_version", "unknown"))
        self.classes = [str(value) for value in self._metadata.get("classes", [])]
        if not self.classes:
            raise InferenceError("model metadata has no classes")

        factory = interpreter_factory or _load_interpreter_factory()
        try:
            try:
                self._interpreter = factory(model_path=str(self.model_path), num_threads=2)
            except TypeError:
                self._interpreter = factory(model_path=str(self.model_path))
            self._interpreter.allocate_tensors()
            inputs = self._interpreter.get_input_details()
            outputs = self._interpreter.get_output_details()
        except Exception as exc:
            raise InferenceError(f"unable to initialize TFLite model: {self.model_path}") from exc
        if len(inputs) != 1 or not outputs:
            raise InferenceError("classifier must expose one input and at least one output")
        self._input = inputs[0]
        self._output = outputs[0]
        shape = [int(value) for value in self._input.get("shape", [])]
        if len(shape) != 4 or shape[0] != 1 or shape[3] != 3:
            raise InferenceError(f"unsupported input shape: {shape}")
        self.height, self.width = shape[1], shape[2]

    @staticmethod
    def _quantization(detail: dict[str, Any]) -> tuple[float, int]:
        scale, zero_point = detail.get("quantization", (0.0, 0))
        return float(scale), int(zero_point)

    def _preprocess(self, image_path: Path) -> Any:
        try:
            import numpy as np

            with Image.open(image_path) as image:
                image = image.convert("RGB").resize(
                    (self.width, self.height), Image.Resampling.BILINEAR
                )
                pixels = np.asarray(image, dtype=np.float32)
        except (OSError, ValueError, ImportError) as exc:
            raise InferenceError(f"unable to read image: {image_path}") from exc

        dtype = np.dtype(self._input["dtype"])
        if dtype.kind in "iu":
            scale, zero_point = self._quantization(self._input)
            if scale <= 0:
                raise InferenceError("quantized input has an invalid scale")
            pixels = np.round(pixels / scale + zero_point)
            info = np.iinfo(dtype)
            pixels = np.clip(pixels, info.min, info.max).astype(dtype)
        else:
            pixels = pixels.astype(dtype)
        return np.expand_dims(pixels, axis=0)

    def _scores(self, output: Any) -> list[float]:
        import numpy as np

        values = np.asarray(output)
        if values.ndim > 1:
            values = values.reshape(-1)
        if values.dtype.kind in "iu":
            scale, zero_point = self._quantization(self._output)
            if scale <= 0:
                raise InferenceError("quantized output has an invalid scale")
            values = (values.astype(np.float32) - zero_point) * scale
        else:
            values = values.astype(np.float32)
        scores = [float(value) for value in values[: len(self.classes)]]
        if len(scores) != len(self.classes) or not all(isfinite(value) for value in scores):
            raise InferenceError("model output does not match the class metadata")
        # Accept either a softmax output or logits from a converted head.
        if any(value < 0 for value in scores) or abs(sum(scores) - 1.0) > 1e-3:
            peak = max(scores)
            scores = [exp(value - peak) for value in scores]
            total = sum(scores)
            scores = [value / total for value in scores] if total else [0.0] * len(scores)
        return scores

    def predict(self, image_path: Path) -> Prediction:
        started = monotonic()
        tensor = self._preprocess(Path(image_path))
        try:
            self._interpreter.set_tensor(self._input["index"], tensor)
            self._interpreter.invoke()
            output = self._interpreter.get_tensor(self._output["index"])
        except Exception as exc:
            raise InferenceError(f"TFLite inference failed for {image_path}") from exc
        scores = self._scores(output)
        best_index = max(range(len(scores)), key=scores.__getitem__)
        return Prediction(
            category=self.classes[best_index],
            confidence=round(scores[best_index], 6),
            model_version=self.model_version,
            inference_time_ms=round((monotonic() - started) * 1000, 3),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
