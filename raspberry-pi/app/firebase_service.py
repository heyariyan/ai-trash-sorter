"""Best-effort Firebase Realtime Database integration.

Physical sorting never waits for Firebase.  Failed remote operations are logged
locally; the machine remains autonomous and safe during an outage.
"""

from __future__ import annotations

import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any


class FirebaseService:
    def __init__(self, *, database_url: str | None, credentials_path=None, storage_bucket: str | None = None) -> None:
        self.database_url = database_url
        self._db = None
        self._bucket = None
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="firebase")
        if not database_url:
            logging.warning("Firebase is not configured; continuing local-only")
            return
        try:
            import firebase_admin
            from firebase_admin import credentials, db, storage

            app_name = "ai-trash-sorter"
            try:
                app = firebase_admin.get_app(app_name)
            except ValueError:
                credential = credentials.Certificate(str(credentials_path)) if credentials_path else credentials.ApplicationDefault()
                options: dict[str, str] = {"databaseURL": database_url}
                if storage_bucket:
                    options["storageBucket"] = storage_bucket
                app = firebase_admin.initialize_app(credential, options, name=app_name)
            self._db = (db, app)
            self._bucket = storage.bucket(app=app) if storage_bucket else None
        except Exception as exc:
            logging.error("Firebase unavailable at startup: %s", exc)

    @property
    def configured(self) -> bool:
        return self._db is not None

    def submit_set(self, path: str, value: dict[str, Any]) -> None:
        self._executor.submit(self._set, path, value)

    def submit_event(self, device_id: str, event_id: str, event: dict[str, Any], max_events: int = 10) -> None:
        self._executor.submit(self._log_and_trim_event, device_id, event_id, event, max_events)

    def _log_and_trim_event(self, device_id: str, event_id: str, event: dict[str, Any], max_events: int) -> None:
        self._set(f"devices/{device_id}/events/{event_id}", event)
        try:
            events_ref = self._reference(f"devices/{device_id}/events")
            if events_ref is not None:
                all_events = events_ref.get()
                if isinstance(all_events, dict) and len(all_events) > max_events:
                    sorted_keys = sorted(
                        all_events.keys(),
                        key=lambda k: str(all_events[k].get("timestamp", "") if isinstance(all_events[k], dict) else "")
                    )
                    excess = len(sorted_keys) - max_events
                    for k in sorted_keys[:excess]:
                        events_ref.child(k).delete()
        except Exception:
            logging.exception("Failed to trim old Firebase events")

    def submit_update(self, path: str, value: dict[str, Any]) -> None:
        self._executor.submit(self._update, path, value)

    def _reference(self, path: str):
        if self._db is None:
            return None
        db, app = self._db
        return db.reference(path.strip("/"), app=app)

    def _set(self, path: str, value: dict[str, Any]) -> None:
        reference = self._reference(path)
        if reference is None:
            return
        try:
            reference.set(value)
        except Exception:
            logging.exception("Firebase set failed: %s", path)

    def _update(self, path: str, value: dict[str, Any]) -> None:
        reference = self._reference(path)
        if reference is None:
            return
        try:
            reference.update(value)
        except Exception:
            logging.exception("Firebase update failed: %s", path)

    def read(self, path: str) -> Any:
        reference = self._reference(path)
        if reference is None:
            return None
        try:
            return reference.get()
        except Exception:
            logging.exception("Firebase read failed: %s", path)
            return None

    def submit_upload_temporary_image(self, local_path, device_id: str, event_id: str) -> None:
        if self._bucket is not None:
            self._executor.submit(self._upload_temporary_image, local_path, device_id, event_id)

    def _upload_temporary_image(self, local_path, device_id: str, event_id: str) -> None:
        try:
            blob = self._bucket.blob(f"devices/{device_id}/temporary/{event_id}.jpg")
            blob.upload_from_filename(str(local_path), content_type="image/jpeg")
            self._update(f"devices/{device_id}/events/{event_id}", {"image_storage_path": blob.name})
        except Exception:
            logging.exception("temporary image upload failed for %s", event_id)

    def submit_retain_image(self, device_id: str, event_id: str, corrected: str, local_path) -> None:
        if self._bucket is not None:
            self._executor.submit(self._retain_image, device_id, event_id, corrected, local_path)

    def _retain_image(self, device_id: str, event_id: str, corrected: str, local_path) -> None:
        try:
            temp = self._bucket.blob(f"devices/{device_id}/temporary/{event_id}.jpg")
            target = self._bucket.blob(f"devices/{device_id}/feedback/{corrected}/{event_id}.jpg")
            if temp.exists():
                self._bucket.copy_blob(temp, self._bucket, target.name)
                temp.delete()
            elif local_path:
                target.upload_from_filename(str(local_path), content_type="image/jpeg")
            self._update(f"devices/{device_id}/events/{event_id}", {"image_storage_path": target.name})
        except Exception:
            logging.exception("feedback image retention upload failed for %s", event_id)

    def submit_delete_temporary_image(self, device_id: str, event_id: str) -> None:
        if self._bucket is not None:
            self._executor.submit(self._delete_temporary_image, device_id, event_id)

    def _delete_temporary_image(self, device_id: str, event_id: str) -> None:
        try:
            self._bucket.blob(f"devices/{device_id}/temporary/{event_id}.jpg").delete()
        except Exception:
            logging.exception("temporary image deletion failed for %s", event_id)

    def publish_status(self, device_id: str, status: dict[str, Any]) -> None:
        status["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.submit_set(f"devices/{device_id}/status", status)

    def close(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=False)


class FirebaseCommandMonitor:
    """Poll calibration commands off the physical control thread."""

    def __init__(self, firebase: FirebaseService, device_id: str, on_calibrate) -> None:
        self.firebase, self.device_id, self.on_calibrate = firebase, device_id, on_calibrate
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name="firebase-commands", daemon=True)

    def start(self) -> None:
        if self.firebase.configured:
            self._thread.start()

    def _run(self) -> None:
        while not self._stop.wait(2.0):
            command = self.firebase.read(f"devices/{self.device_id}/commands/calibrate")
            if isinstance(command, dict) and command.get("requested") is True:
                self.on_calibrate()
                self.firebase.submit_update(f"devices/{self.device_id}/commands/calibrate", {"requested": False, "acknowledged_at": datetime.now(timezone.utc).isoformat()})

    def close(self) -> None:
        self._stop.set()
        if self._thread.is_alive():
            self._thread.join(timeout=3)
