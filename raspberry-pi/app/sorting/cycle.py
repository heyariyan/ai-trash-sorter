"""Offline AI-to-bin cycle orchestration without camera or ultrasonic I/O.

The caller supplies an image path (for example, an image already in the Pi's
Pictures directory). The cycle predicts, moves to the selected logical bin,
opens the gate, closes it, and returns measured stage timings. Boot homing is a
separate explicit operation and must complete before ``run`` is called.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import monotonic

from ai.inference import Prediction, TFLiteModel
from .positioning import PositionPlan, SorterPositionController


@dataclass(frozen=True)
class SortCycleResult:
    image_path: Path
    prediction: Prediction
    position_plan: PositionPlan
    timings_ms: dict[str, float]


class SortingCycle:
    """Compose model, calibrated position controller, and servo gate."""

    def __init__(
        self,
        model: TFLiteModel,
        position_controller: SorterPositionController,
        gate,
    ) -> None:
        self.model = model
        self.position_controller = position_controller
        self.gate = gate

    def run(self, image_path: Path, on_prediction=None) -> SortCycleResult:
        if not self.position_controller.calibrated:
            raise RuntimeError("sorter must be calibrated before a sorting cycle")
        image_path = Path(image_path)
        total_started = monotonic()

        prediction_started = monotonic()
        prediction = self.model.predict(image_path)
        prediction_ms = (monotonic() - prediction_started) * 1000
        if callable(on_prediction):
            on_prediction(prediction)

        move_started = monotonic()
        plan = self.position_controller.move_to(prediction.category)
        move_ms = (monotonic() - move_started) * 1000

        open_started = monotonic()
        self.gate.open()
        gate_open_ms = (monotonic() - open_started) * 1000

        close_started = monotonic()
        self.gate.close()
        gate_close_ms = (monotonic() - close_started) * 1000

        timings_ms = {
            "prediction_ms": round(prediction_ms, 3),
            "position_ms": round(move_ms, 3),
            "gate_open_ms": round(gate_open_ms, 3),
            "gate_close_ms": round(gate_close_ms, 3),
            "total_cycle_ms": round((monotonic() - total_started) * 1000, 3),
        }
        return SortCycleResult(
            image_path=image_path,
            prediction=prediction,
            position_plan=plan,
            timings_ms=timings_ms,
        )
