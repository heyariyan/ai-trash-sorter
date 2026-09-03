"""Capture-only camera adapters.

The sorting state machine depends on the small :class:`Camera` interface and
does not import GPIO or Picamera2 directly.  ``MockCamera`` is safe for local
tests and simulation mode; ``Picamera2Camera`` is loaded only on a Pi with
Picamera2 installed.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import monotonic, sleep
from typing import Any, Protocol


class CameraError(RuntimeError):
    """Raised when the camera cannot be started or capture cannot complete."""


@dataclass(frozen=True)
class CaptureResult:
    """Metadata for one captured frame."""

    path: Path
    captured_at: str
    width: int
    height: int
    capture_time_ms: float
    simulated: bool


class Camera(Protocol):
    """Minimal camera contract used by the runtime and tests."""

    def start(self) -> None:
        """Initialize the camera and leave it warm for capture."""

    def capture(self, destination: Path) -> CaptureResult:
        """Capture one frame to ``destination``."""

    def stop(self) -> None:
        """Release camera resources."""


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


class Picamera2Camera:
    """Picamera2 still-image adapter for Raspberry Pi OS."""

    def __init__(self, width: int = 640, height: int = 480, warmup_seconds: float = 1.0) -> None:
        if width <= 0 or height <= 0:
            raise ValueError("camera dimensions must be positive")
        if warmup_seconds < 0:
            raise ValueError("warmup_seconds must not be negative")
        self.width = width
        self.height = height
        self.warmup_seconds = warmup_seconds
        self._camera: Any | None = None

    def start(self) -> None:
        if self._camera is not None:
            return
        try:
            from picamera2 import Picamera2
        except ImportError as exc:  # pragma: no cover - exercised on Pi
            raise CameraError(
                "Picamera2 is unavailable; install it on the Raspberry Pi before capture"
            ) from exc

        try:
            camera = Picamera2()
            # Preview configuration provides ultra-fast buffered memory frames (instantaneous, no locking)
            configuration = camera.create_preview_configuration(
                main={"size": (self.width, self.height), "format": "RGB888"}
            )
            camera.configure(configuration)
            camera.start()
            if self.warmup_seconds:
                sleep(self.warmup_seconds)
        except Exception as exc:  # pragma: no cover - hardware-specific
            try:
                camera.close()
            except Exception:
                pass
            raise CameraError(f"unable to start Picamera2: {exc}") from exc
        self._camera = camera

    def capture(self, destination: Path) -> CaptureResult:
        if self._camera is None:
            self.start()
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        started = monotonic()
        try:
            from PIL import Image
            # Instantaneous memory capture (< 15ms)
            frame = self._camera.capture_array("main")
            img = Image.fromarray(frame)
            img.save(str(destination), "JPEG", quality=85)
        except Exception as exc:
            try:
                self._camera.capture_file(str(destination))
            except Exception as inner_exc:
                try:
                    self.stop()
                    self.start()
                except Exception:
                    pass
                raise CameraError(f"camera capture failed: {inner_exc}") from exc
        return CaptureResult(
            path=destination,
            captured_at=_timestamp(),
            width=self.width,
            height=self.height,
            capture_time_ms=round((monotonic() - started) * 1000, 3),
            simulated=False,
        )

    def stop(self) -> None:
        if self._camera is None:
            return
        try:
            self._camera.stop()
        finally:
            self._camera.close()
            self._camera = None


class MockCamera:
    """Deterministic capture adapter for simulation and unit tests."""

    def __init__(self, width: int = 640, height: int = 480, capture_delay_seconds: float = 0.0) -> None:
        if width <= 0 or height <= 0:
            raise ValueError("camera dimensions must be positive")
        if capture_delay_seconds < 0:
            raise ValueError("capture_delay_seconds must not be negative")
        self.width = width
        self.height = height
        self.capture_delay_seconds = capture_delay_seconds
        self.started = False
        self.capture_count = 0

    def start(self) -> None:
        self.started = True

    def capture(self, destination: Path) -> CaptureResult:
        if not self.started:
            raise CameraError("camera is not started")
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        started = monotonic()
        if self.capture_delay_seconds:
            sleep(self.capture_delay_seconds)
        self.capture_count += 1
        destination.write_bytes(
            f"SIMULATED_IMAGE frame={self.capture_count} width={self.width} height={self.height}\n".encode()
        )
        return CaptureResult(
            path=destination,
            captured_at=_timestamp(),
            width=self.width,
            height=self.height,
            capture_time_ms=round((monotonic() - started) * 1000, 3),
            simulated=True,
        )

    def stop(self) -> None:
        self.started = False
