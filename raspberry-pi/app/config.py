"""Single configuration surface for the autonomous sorter."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any


DEFAULT_BINS = ("BIODEGRADABLE", "PLASTIC", "METAL", "OTHER")


@dataclass(frozen=True)
class SorterConfig:
    device_id: str = "rpi-sorter-01"
    model_path: Path = Path("/opt/ai-trash-sorter/model/model.tflite")
    model_metadata_path: Path | None = None
    data_dir: Path = Path("/var/lib/ai-trash-sorter")
    trigger_distance_cm: float = 7.0
    minimum_distance_cm: float = 0.0
    presence_samples: int = 2
    clear_samples: int = 2
    poll_seconds: float = 0.05
    confidence_threshold: float | None = 0.75
    camera_width: int = 640
    camera_height: int = 480
    camera_warmup_seconds: float = 1.0
    u1_trigger_gpio: int = 4
    u1_echo_gpio: int = 5
    u3_trigger_gpio: int = 27
    u3_echo_gpio: int = 13
    home_gpio: int = 23
    home_direction: int = 0
    home_max_steps: int = 1000
    home_timeout_seconds: float = 20.0
    step_gpio: int = 24
    direction_gpio: int = 25
    enable_gpio: int = 8
    reset_gpio: int = 7
    sleep_gpio: int = 9
    steps_per_revolution: int = 200
    step_pulse_seconds: float = 0.005
    forward_direction: int = 1
    bin_order: tuple[str, ...] = DEFAULT_BINS
    servo_gpio: int = 18
    servo_closed_angle: float = 0.0
    servo_open_angle: float = 90.0
    servo_reverse: bool = False
    gate_settle_seconds: float = 0.70
    drop_delay_seconds: float = 0.60
    post_drop_settle_seconds: float = 0.20
    failed_image_retention: bool = True
    temporary_image_ttl_seconds: int = 86400
    firebase_database_url: str | None = None
    firebase_credentials_path: Path | None = None
    firebase_storage_bucket: str | None = None
    firebase_timeout_seconds: float = 5.0
    display: str = "console"
    feedback_timeout_seconds: float = 8.0
    yes_gpio: int = 20
    no_gpio: int = 21
    prev_gpio: int = 16
    next_gpio: int = 12
    firebase_max_events: int = 10

    def __post_init__(self) -> None:
        for attr in ("model_path", "data_dir"):
            val = getattr(self, attr)
            if isinstance(val, str):
                object.__setattr__(self, attr, Path(val))
        for attr in ("model_metadata_path", "firebase_credentials_path"):
            val = getattr(self, attr)
            if isinstance(val, str):
                object.__setattr__(self, attr, Path(val))
        if isinstance(self.bin_order, (list, tuple)):
            object.__setattr__(self, "bin_order", tuple(str(item).upper() for item in self.bin_order))

    @property
    def temp_images_dir(self) -> Path:
        return self.data_dir / "images" / "temp"

    @property
    def feedback_images_dir(self) -> Path:
        return self.data_dir / "images" / "feedback"

    @property
    def diagnostics_images_dir(self) -> Path:
        return self.data_dir / "images" / "diagnostics"

    @property
    def journal_dir(self) -> Path:
        return self.data_dir / "journal"

    def validate(self) -> None:
        if self.trigger_distance_cm <= 0 or self.minimum_distance_cm >= self.trigger_distance_cm:
            raise ValueError("trigger distance must be positive and greater than minimum distance")
        if self.steps_per_revolution <= 0 or self.steps_per_revolution % len(self.bin_order):
            raise ValueError("steps_per_revolution must divide evenly across bins")
        if len(self.bin_order) != 4 or len(set(self.bin_order)) != 4:
            raise ValueError("bin_order must contain four unique categories")
        if self.home_direction not in (0, 1) or self.forward_direction not in (0, 1):
            raise ValueError("directions must be 0 or 1")
        if self.home_max_steps <= 0 or self.home_timeout_seconds <= 0 or self.step_pulse_seconds <= 0:
            raise ValueError("homing and step timing values must be positive")
        if self.temporary_image_ttl_seconds < 0:
            raise ValueError("temporary image TTL must not be negative")
        if self.display not in ("console", "ssd1306"):
            raise ValueError("display must be console or ssd1306")


def load_config(path: Path | None = None) -> SorterConfig:
    """Load an optional JSON file; secrets stay outside version control."""

    values: dict[str, Any] = {}
    if path is None:
        # Check standard search locations
        for candidate in (
            Path("/etc/ai-trash-sorter/config.json"),
            Path("config.json"),
            Path("raspberry-pi/config.json"),
        ):
            if candidate.exists():
                path = candidate
                break

    if path and Path(path).exists():
        try:
            values = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"invalid configuration file: {path}") from exc
    elif path:
        raise ValueError(f"configuration file not found: {path}")

    allowed = {item.name for item in fields(SorterConfig)}
    unknown = set(values) - allowed
    if unknown:
        raise ValueError(f"unknown configuration keys: {', '.join(sorted(unknown))}")
    for key in ("model_path", "model_metadata_path", "data_dir", "firebase_credentials_path"):
        if values.get(key) is not None:
            values[key] = Path(values[key])
    if "bin_order" in values:
        values["bin_order"] = tuple(str(item).upper() for item in values["bin_order"])
    config = SorterConfig(**values)
    config.validate()
    return config
