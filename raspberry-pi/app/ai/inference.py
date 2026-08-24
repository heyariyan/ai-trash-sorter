"""Pi-compatible inference for the transparent M3 RGB-centroid baseline."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from math import exp
from pathlib import Path
from time import monotonic

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


class RgbCentroidModel:
    def __init__(self, model_path: Path) -> None:
        try:
            self._model = json.loads(Path(model_path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise InferenceError(f"unable to load model: {model_path}") from exc
        if self._model.get("format") != "rgb_centroid_v1":
            raise InferenceError("unsupported model format")
        self.model_version = str(self._model["model_version"])
        self.image_size = int(self._model["image_size"])
        self.centroids: dict[str, list[float]] = self._model["centroids"]
        if not self.centroids:
            raise InferenceError("model has no class centroids")

    def _feature(self, image_path: Path) -> list[float]:
        try:
            with Image.open(image_path) as image:
                image = image.convert("RGB").resize(
                    (self.image_size, self.image_size), Image.Resampling.BILINEAR
                )
                pixels = image.load()
                return [
                    channel / 255.0
                    for y in range(self.image_size)
                    for x in range(self.image_size)
                    for channel in pixels[x, y]
                ]
        except (OSError, ValueError) as exc:
            raise InferenceError(f"unable to read image: {image_path}") from exc

    @staticmethod
    def _distance(left: list[float], right: list[float]) -> float:
        return sum((a - b) ** 2 for a, b in zip(left, right)) ** 0.5

    def predict(self, image_path: Path) -> Prediction:
        started = monotonic()
        feature = self._feature(Path(image_path))
        distances = {label: self._distance(feature, centroid) for label, centroid in self.centroids.items()}
        scores = {label: exp(-value) for label, value in distances.items()}
        total = sum(scores.values())
        category = min(distances, key=distances.get)
        confidence = scores[category] / total if total else 0.0
        return Prediction(
            category=category,
            confidence=confidence,
            model_version=self.model_version,
            inference_time_ms=round((monotonic() - started) * 1000, 3),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
