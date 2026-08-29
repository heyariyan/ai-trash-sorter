"""Local-first PocketBase writer with JSONL buffering.

Sorting must continue when PocketBase is down. This store writes each record to
local JSONL first, then queues an optional PocketBase POST on a background
thread so HTTP latency cannot block the physical cycle.
"""

from __future__ import annotations

import json
import queue
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error, request


class PocketBaseError(RuntimeError):
    """Raised when a PocketBase API operation fails."""


@dataclass(frozen=True)
class PocketBaseClient:
    base_url: str
    auth_token: str | None = None
    timeout_seconds: float = 1.0

    def post_record(self, collection: str, fields: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url.rstrip('/')}/api/collections/{collection}/records"
        body = json.dumps(fields).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = self.auth_token
        req = request.Request(url, data=body, headers=headers, method="POST")
        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except (OSError, error.HTTPError, json.JSONDecodeError) as exc:
            raise PocketBaseError(f"PocketBase write failed for {collection}") from exc

    def get_setting(self, key: str) -> dict[str, Any] | None:
        url = f"{self.base_url.rstrip('/')}/api/collections/settings/records?filter=(key='{key}')"
        req = request.Request(url, method="GET")
        if self.auth_token:
            req.add_header("Authorization", self.auth_token)
        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as response:
                data = json.loads(response.read().decode("utf-8"))
                items = data.get("items", [])
                return items[0] if items else None
        except Exception:
            return None


class LocalFirstEventStore:
    """Write local JSONL immediately and mirror to PocketBase asynchronously."""

    def __init__(
        self,
        *,
        buffer_dir: Path,
        pocketbase: PocketBaseClient | None = None,
        device_id: str = "rpi-local",
    ) -> None:
        self.buffer_dir = Path(buffer_dir)
        self.pocketbase = pocketbase
        self.device_id = device_id
        self.buffer_dir.mkdir(parents=True, exist_ok=True)
        self._queue: queue.Queue[tuple[str, dict[str, Any]] | None] = queue.Queue()
        self._failures_path = self.buffer_dir / "pocketbase-failed.jsonl"
        self._worker: threading.Thread | None = None
        if self.pocketbase is not None:
            self._worker = threading.Thread(target=self._sync_worker, daemon=True)
            self._worker.start()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def check_calibration_trigger(self) -> bool:
        """Check for external calibration requests from trigger file or settings."""
        trigger_file = self.buffer_dir / "calibrate.trigger"
        if trigger_file.exists():
            try:
                trigger_file.unlink()
                return True
            except Exception:
                return True
        return False

    def _append_jsonl(self, filename: str, record: dict[str, Any]) -> None:
        path = self.buffer_dir / filename
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")

    def _queue_remote(self, collection: str, record: dict[str, Any]) -> None:
        if self.pocketbase is not None:
            self._queue.put((collection, record))

    def _sync_worker(self) -> None:
        while True:
            item = self._queue.get()
            try:
                if item is None:
                    return
                collection, record = item
                try:
                    self.pocketbase.post_record(collection, record)
                except PocketBaseError:
                    self._append_jsonl(
                        "pocketbase-failed.jsonl",
                        {"collection": collection, "record": record, "failed_at": self._now()},
                    )
            finally:
                self._queue.task_done()

    def save_sorting_event(self, fields: dict[str, Any]) -> str:
        local_id = str(uuid.uuid4())
        record = {
            "local_id": local_id,
            "device_id": self.device_id,
            "timestamp": self._now(),
            **fields,
        }
        self._append_jsonl("sorting-events.jsonl", record)
        self._queue_remote("sorting_events", record)
        return local_id

    def save_feedback(self, fields: dict[str, Any]) -> str:
        local_id = str(uuid.uuid4())
        record = {"local_id": local_id, "timestamp": self._now(), **fields}
        self._append_jsonl("feedback.jsonl", record)
        self._queue_remote("feedback", record)
        return local_id

    def save_bin_status(self, fields: dict[str, Any]) -> str:
        local_id = str(uuid.uuid4())
        record = {"local_id": local_id, "timestamp": self._now(), **fields}
        self._append_jsonl("bin-status.jsonl", record)
        self._queue_remote("settings", {"key": "latest_bin_status", "value": record})
        return local_id

    def close(self, *, wait: bool = False) -> None:
        if self._worker is None:
            return
        if wait:
            self._queue.join()
        self._queue.put(None)
