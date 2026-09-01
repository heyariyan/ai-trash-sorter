"""The one deterministic, autonomous waste-sorting state machine."""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from time import monotonic, sleep

from ai.inference import InferenceError
from firebase_service import FirebaseCommandMonitor


class SorterState(str, Enum):
    STARTING = "STARTING"
    HOMING = "HOMING"
    READY = "READY"
    DETECTED = "DETECTED"
    CAPTURING = "CAPTURING"
    CLASSIFYING = "CLASSIFYING"
    MOVING = "MOVING"
    DROPPING = "DROPPING"
    MEASURING = "MEASURING"
    WAITING_FOR_CLEAR = "WAITING_FOR_CLEAR"
    ERROR = "ERROR"


class AutonomousSorter:
    def __init__(self, *, config, detector, camera, model, position, gate, bin_sensor, firebase, retention, display=None) -> None:
        self.config, self.detector, self.camera, self.model = config, detector, camera, model
        self.position, self.gate, self.bin_sensor = position, gate, bin_sensor
        self.firebase, self.retention, self.display = firebase, retention, display
        self.state = SorterState.STARTING
        self.last_prediction = None
        self._waiting_for_clear = False
        self._home_requested = False
        self._u1_invalid_reported = False
        self._command_monitor = FirebaseCommandMonitor(firebase, config.device_id, self._queue_home)

    def _set_state(self, state: SorterState, message: str = "") -> None:
        self.state = state
        logging.info("state=%s %s", state.value, message)
        if self.display:
            self.display.show_status(message or state.value)
        self.firebase.publish_status(self.config.device_id, self.status())

    def status(self) -> dict:
        return {"state": self.state.value, "current_position": self.position.current_stop, "position_known": self.position.calibrated, "last_detected_class": getattr(self.last_prediction, "category", None), "confidence": getattr(self.last_prediction, "confidence", None), "model_version": getattr(self.model, "model_version", "unknown")}

    def start(self) -> None:
        self._set_state(SorterState.STARTING, "Starting")
        self.camera.start()  # warm camera once
        self.retention.start()
        self._command_monitor.start()
        self.gate.close()
        self.home()

    def home(self) -> None:
        self._set_state(SorterState.HOMING, "Homing carousel")
        try:
            self.position.calibrate(
                home_direction=self.config.home_direction,
                max_home_steps=self.config.home_max_steps,
                home_timeout_seconds=self.config.home_timeout_seconds,
            )
        except Exception:
            self.position.invalidate_position()
            self._safe_close_gate()
            self._set_state(SorterState.ERROR, "Homing failed; position unknown")
            raise
        self._waiting_for_clear = False
        self._set_state(SorterState.READY, "Ready")

    def request_home(self) -> None:
        """Perform only while idle; Firebase commands call this at the next idle tick."""
        if self.state in (SorterState.READY, SorterState.ERROR):
            self.home()

    def _queue_home(self) -> None:
        self._home_requested = True

    def tick(self) -> dict | None:
        if self._home_requested and self.state == SorterState.READY:
            self._home_requested = False
            self.home()
            return None
        if self.state == SorterState.ERROR:
            return None
        reading = self.detector.poll()
        if not reading.valid:
            if not self._u1_invalid_reported:
                logging.warning("U1 invalid reading; no physical action")
                self._u1_invalid_reported = True
            return None
        self._u1_invalid_reported = False
        if self._waiting_for_clear:
            if not reading.present:
                self._waiting_for_clear = False
                self._set_state(SorterState.READY, "Ready")
            return None
        if self.state != SorterState.READY or not reading.present:
            return None
        return self._run_cycle(reading)

    def _run_cycle(self, presence) -> dict:
        event_id = str(uuid.uuid4())
        total_started = monotonic()
        capture_path = self.config.temp_images_dir / f"{event_id}.jpg"
        self._set_state(SorterState.DETECTED, "Object detected")
        try:
            self._set_state(SorterState.CAPTURING, "Capturing")
            capture = self.camera.capture(capture_path)
            self._set_state(SorterState.CLASSIFYING, "Classifying")
            prediction = self.model.predict(capture.path)
            self.last_prediction = prediction
            if self.display:
                self.display.show_prediction(prediction.category, prediction.confidence)
            category = prediction.category.upper()
            if category not in self.config.bin_order:
                raise InferenceError(f"model returned unsupported category: {category}")
            if self.config.confidence_threshold is not None and prediction.confidence < self.config.confidence_threshold:
                raise InferenceError(f"confidence {prediction.confidence} below threshold")
        except Exception as exc:
            self._failed_event(event_id, capture_path, "inference", str(exc))
            self._waiting_for_clear = True
            self._set_state(SorterState.WAITING_FOR_CLEAR, "Classification failed")
            return {"event_id": event_id, "status": "classification_failed"}

        try:
            self._set_state(SorterState.MOVING, f"Moving to {category}")
            plan = self.position.move_to(category)
        except Exception as exc:
            self.position.invalidate_position()
            self._safe_close_gate()
            self._failed_event(event_id, capture_path, "movement", str(exc))
            self._set_state(SorterState.ERROR, "Movement failed; home required")
            return {"event_id": event_id, "status": "movement_failed"}

        try:
            self._set_state(SorterState.DROPPING, f"Dropping into {category}")
            self.gate.open()
            sleep(self.config.drop_delay_seconds)
            self.gate.close()
            self._set_state(SorterState.MEASURING, "Measuring bin")
            sleep(self.config.post_drop_settle_seconds)
            bin_distance = self.bin_sensor.read_distance_cm() if self.bin_sensor else None
            if self.display:
                self.display.show_bin_status(category, bin_distance)
        except Exception as exc:
            self._safe_close_gate()
            self._failed_event(event_id, capture_path, "gate_or_bin_measurement", str(exc))
            self._waiting_for_clear = True
            self._set_state(SorterState.WAITING_FOR_CLEAR, "Drop measurement failed")
            return {"event_id": event_id, "status": "drop_failed"}

        timestamp = prediction.timestamp
        event = {"event_id": event_id, "timestamp": timestamp, "detected_class": category, "confidence": prediction.confidence, "selected_bin": category, "model_version": prediction.model_version, "inference_time_ms": prediction.inference_time_ms, "sorting_time_ms": round((monotonic() - total_started) * 1000, 3), "movement_steps": plan.steps, "movement_direction": plan.direction, "bin_distance_cm": bin_distance, "feedback_status": "pending", "image_state": "temporary"}
        self._append_journal(event)
        self.firebase.submit_set(f"devices/{self.config.device_id}/events/{event_id}", event)
        self.firebase.submit_update(f"devices/{self.config.device_id}/bins/{category}", {"distance_cm": bin_distance, "updated_at": timestamp})
        self.retention.register(event_id=event_id, image_path=capture.path, prediction=category, timestamp=timestamp)
        self._waiting_for_clear = True
        self._set_state(SorterState.WAITING_FOR_CLEAR, "Remove next object")
        return {"status": "sorted", **event, "position": asdict(plan), "camera_capture_ms": capture.capture_time_ms, "sensor_distance_cm": presence.distance_cm}

    def _failed_event(self, event_id: str, image_path: Path, stage: str, error: str) -> None:
        self._safe_close_gate()
        self.retention.retain_diagnostic(image_path, event_id)
        event = {"event_id": event_id, "timestamp": datetime.now(timezone.utc).isoformat(), "success": False, "failure_stage": stage, "error": error, "feedback_status": "unavailable", "image_state": "diagnostic" if self.config.failed_image_retention else "deleted"}
        self._append_journal(event)
        self.firebase.submit_set(f"devices/{self.config.device_id}/events/{event_id}", event)
        if self.display:
            self.display.show_error(f"{stage}: {error}")
        logging.error("cycle %s failed at %s: %s", event_id, stage, error)

    def _append_journal(self, event: dict) -> None:
        self.config.journal_dir.mkdir(parents=True, exist_ok=True)
        with (self.config.journal_dir / "events.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, sort_keys=True) + "\n")

    def _safe_close_gate(self) -> None:
        try:
            self.gate.close()
        except Exception:
            logging.exception("unable to close gate")

    def close(self) -> None:
        self._safe_close_gate()
        self._command_monitor.close()
        self.retention.close()
        for component in (self.camera, self.position.stepper, self.position.home_sensor, self.bin_sensor, getattr(self.gate, "servo", None), self.firebase):
            close = getattr(component, "close", None)
            stop = getattr(component, "stop", None)
            try:
                if callable(close): close()
                elif callable(stop): stop()
            except Exception:
                logging.exception("shutdown failed for %s", component)
