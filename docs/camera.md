# M2 camera capture

Status: **Implemented capture abstraction; Pi capture pending a connected-camera test.**

## Design

The runtime uses the small `Camera` interface in `raspberry-pi/app/camera/camera.py`. The state machine can depend on that interface without importing GPIO or a camera vendor library.

- `Picamera2Camera` is the Raspberry Pi adapter.
- `MockCamera` is deterministic and safe for simulation/unit tests.
- The camera is started once and kept warm; capture does not reinitialize it.
- Every capture returns the path, UTC timestamp, dimensions, simulation flag, and measured `capture_time_ms`.
- Capture errors raise `CameraError`; callers can take a safe non-actuating exit.

## Capture policy

U1's fixed intake sensor will trigger the capture workflow in a later milestone. M2 itself is capture-only: no stepper, servo, bin selection, or cloud/database call is involved.

Images should be written beneath the runtime data directory (eventually `/var/lib/ai-trash-sorter/images/`) and not committed to Git. The checked-in mock writes a marker payload, not a real photograph.

## Pi verification procedure

Run only after Picamera2 is installed and the camera ribbon cable has been inspected:

```text
1. Confirm the Pi is stationary and all motor power is disabled.
2. Start the camera adapter in capture-only mode.
3. Capture ten frames to a temporary runtime directory.
4. Record each capture_time_ms and inspect the files for valid images.
5. Stop the camera and confirm the process exits cleanly.
```

Do not connect this test to the sorter state machine until the capture files and timings are verified.

## Command

From `raspberry-pi/app/`, simulation mode is safe on any machine with Python:

```text
AI_TRASH_SORTER_SIMULATION=true python -m camera.capture_once --output captures/test.jpg
```

On the Pi, remove the simulation setting only after Picamera2 and the camera ribbon connection have been verified:

```text
python -m camera.capture_once --output /var/lib/ai-trash-sorter/images/m2-test.jpg
```

## Benchmark fields

Record measured values, not claims:

`camera_capture_ms`, `image_width`, `image_height`, `file_size_bytes`, `capture_success`, and `timestamp`.
