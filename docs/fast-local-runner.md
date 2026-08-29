# Fast local sorter runner

Status: **Software and local hardware interfaces complete and verified; full physical run supported with hardware diagnostics.**

`raspberry-pi/app/runner/local_runner.py` composes the fast offline appliance loop:

1. Start camera/model resources and close the gate.
2. Calibrate once at boot using GPIO23 IR home.
3. Check for external calibration triggers (`request_calibration()`, file trigger `runtime/calibrate.trigger`, or app request).
4. Poll U1 until an object is detected within 7 cm.
5. Capture an image with the warm Raspberry Pi camera.
6. Run the TFLite model and display the prediction with confidence bar on OLED / console.
7. Move the four-stop carousel by the shortest path.
8. Fast servo gate cycle: open, drop waste, close (snappy 0.2s settle).
9. Read U3 as the post-drop bin-status sensor and display bin level.
10. Prompt for YES/NO feedback and interactive corrected label selection menu.
11. Write sorting event, feedback, and bin-status data locally to JSONL; queue async PocketBase sync.

The runner exposes `request_calibration()` and watches `runtime/calibrate.trigger` for the upcoming app calibration button. It calibrates at boot, then recalibrates only when requested or after an error.

## Fast-path settings

Default runtime values:

| Setting | Value |
| --- | ---: |
| U1 presence threshold | <= 7 cm |
| Stepper effective revolution | 600 steps |
| Stepper pulse delay | 3 ms |
| Gate settle delay | 0.20 s |
| Post-drop settle delay | 0.20 s |
| Feedback timeout | 8 s |
| U1 trigger/echo | GPIO4 / GPIO5 |
| U3 trigger/echo | GPIO27 / GPIO13 |

## Diagnostic & Hardware Test Commands

### 1. Unified Local System Diagnostic
Run the full local system diagnostic (homing, servo gate, ultrasonics, display, event store):

```bash
# Simulation mode:
PYTHONPATH=/opt/ai-trash-sorter/app python -m runner.system_test --simulation

# Physical hardware verification (on Pi):
PYTHONPATH=/opt/ai-trash-sorter/app python -m runner.system_test --confirm-movement
```

### 2. Dual Ultrasonic Sensor Test (U1 & U3)
Stream live distance readings from U1 (intake) and U3 (bin fill):

```bash
# Live ultrasonic stream:
PYTHONPATH=/opt/ai-trash-sorter/app python -m sensors.ultrasonic_test \
  --u1-trig 4 --u1-echo 5 --u3-trig 27 --u3-echo 13 --presence-threshold-cm 7.0
```

### 3. OLED Display Screen Test
Cycle through all OLED graphical screens (Ready, Prediction, Bin Status, Feedback, Correction Menu, Error):

```bash
# Physical OLED (I2C GPIO2/GPIO3):
PYTHONPATH=/opt/ai-trash-sorter/app python -m display.display_test --display ssd1306

# Console simulation:
PYTHONPATH=/opt/ai-trash-sorter/app python -m display.display_test --display console
```

### 4. Immediate Stepper Calibration
Calibrate home position immediately on demand and exit:

```bash
PYTHONPATH=/opt/ai-trash-sorter/app python -m runner.local_runner \
  --calibrate-now --confirm-movement
```

### 5. Fast Sorting Loop Command
Run the continuous fast appliance loop:

```bash
PYTHONPATH=/opt/ai-trash-sorter/app python -m runner.local_runner \
  --model /opt/ai-trash-sorter/model/waste-mobilenet-taco-kaggle-v1.tflite \
  --confirm-movement \
  --steps-per-revolution 600 \
  --stepper-pulse-delay-ms 3 \
  --gate-settle-seconds 0.2 \
  --presence-threshold-cm 7 \
  --u1-trig 4 --u1-echo 5 \
  --bin-trig 27 --bin-echo 13 \
  --display ssd1306
```

PocketBase is never allowed to block sorting. Events and feedback are written to local JSONL first and queued for async sync when PocketBase is configured.
