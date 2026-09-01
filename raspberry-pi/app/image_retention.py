"""Temporary capture lifecycle and asynchronous correction retention."""

from __future__ import annotations

import json
import logging
import shutil
import threading
from datetime import datetime, timezone
from pathlib import Path
from time import sleep
from typing import Any


class ImageRetentionManager:
    """Keeps a bounded temporary window; only incorrect feedback becomes permanent."""

    def __init__(self, config, firebase) -> None:
        self.config = config
        self.firebase = firebase
        self.pending_file = config.journal_dir / "pending-images.json"
        self._pending: dict[str, dict[str, Any]] = self._load()
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name="feedback-retention", daemon=True)

    def start(self) -> None:
        for directory in (self.config.temp_images_dir, self.config.feedback_images_dir, self.config.diagnostics_images_dir, self.config.journal_dir):
            directory.mkdir(parents=True, exist_ok=True)
        self._thread.start()

    def register(self, *, event_id: str, image_path: Path, prediction: str, timestamp: str) -> None:
        with self._lock:
            self._pending[event_id] = {"path": str(image_path), "prediction": prediction, "timestamp": timestamp}
            self._save()
        self.firebase.submit_upload_temporary_image(image_path, self.config.device_id, event_id)

    def retain_diagnostic(self, image_path: Path, event_id: str) -> None:
        if not image_path.exists() or not self.config.failed_image_retention:
            image_path.unlink(missing_ok=True)
            return
        target = self.config.diagnostics_images_dir / f"{event_id}.jpg"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(image_path), str(target))

    def _load(self) -> dict[str, dict[str, Any]]:
        try:
            return json.loads(self.pending_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}

    def _save(self) -> None:
        self.pending_file.parent.mkdir(parents=True, exist_ok=True)
        self.pending_file.write_text(json.dumps(self._pending, indent=2, sort_keys=True), encoding="utf-8")

    def _run(self) -> None:
        while not self._stop.wait(2.0):
            self.process_once()

    def process_once(self) -> None:
        now = datetime.now(timezone.utc)
        with self._lock:
            pending = list(self._pending.items())
        for event_id, record in pending:
            feedback = self.firebase.read(f"devices/{self.config.device_id}/feedback/{event_id}")
            if isinstance(feedback, dict) and feedback.get("status") == "incorrect":
                corrected = str(feedback.get("corrected_category", "")).upper()
                if corrected in self.config.bin_order:
                    self._retain(event_id, record, corrected)
                    continue
            if isinstance(feedback, dict) and feedback.get("status") == "correct":
                self._discard(event_id, record, "confirmed_correct")
                continue
            try:
                age = (now - datetime.fromisoformat(record["timestamp"])).total_seconds()
            except (ValueError, KeyError):
                age = self.config.temporary_image_ttl_seconds + 1
            if age >= self.config.temporary_image_ttl_seconds:
                self._discard(event_id, record, "expired")

    def _retain(self, event_id: str, record: dict[str, Any], corrected: str) -> None:
        source = Path(record["path"])
        stamp = record["timestamp"].replace(":", "-").replace("+", "_")
        target = self.config.feedback_images_dir / corrected / f"{stamp}_{event_id}_pred-{record['prediction']}_label-{corrected}.jpg"
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.exists():
            shutil.move(str(source), str(target))
        self.firebase.submit_retain_image(self.config.device_id, event_id, corrected, target)
        self._finish(event_id)
        self.firebase.submit_update(f"devices/{self.config.device_id}/events/{event_id}", {"feedback_status": "corrected", "corrected_category": corrected, "image_state": "retained"})

    def _discard(self, event_id: str, record: dict[str, Any], reason: str) -> None:
        Path(record["path"]).unlink(missing_ok=True)
        self.firebase.submit_delete_temporary_image(self.config.device_id, event_id)
        self._finish(event_id)
        self.firebase.submit_update(f"devices/{self.config.device_id}/events/{event_id}", {"image_state": "deleted", "image_cleanup_reason": reason})

    def _finish(self, event_id: str) -> None:
        with self._lock:
            self._pending.pop(event_id, None)
            self._save()

    def close(self) -> None:
        self._stop.set()
        self._thread.join(timeout=3)
