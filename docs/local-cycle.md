# M8 offline local sorting cycle

Status: **Software, simulation, and guarded physical actuator cycles exercised; latest slow visual recheck pending developer observation.**

This milestone composes only the local path requested for the first integrated
test:

1. Start and home the stepper using GPIO23.
2. Run the quantized neural model on an existing image file.
3. Choose the material bin and move by the shortest calibrated path.
4. Open the GPIO18 MG995 gate at 90 degrees.
5. Close the gate at 0 degrees.
6. Report prediction, position plan, and measured stage/total timings.

The camera and ultrasonic sensors are deliberately excluded. Two existing Pi
image paths can be supplied to `motors`/`sorting.local_cycle_test`; no image is
captured during this test.

The physical command requires an explicit effective carousel
`--steps-per-revolution` value. The earlier 200-pulse observation produced only
about 120 degrees, so 200 must not be assumed for the installed mechanism.

The combined test is safety-sensitive because it energizes both the stepper and
servo in one sequence. Confirm the already-tested stepper/IR/servo conditions,
keep the mechanism clear, and authorize the combined cycle immediately before
running it. The command always homes first and shuts down all GPIO resources in
`finally`.

## Pi AI-only image checks

Before any combined actuator test, two existing images were run through the
offline Pi model without camera or ultrasonic access:

| Image | Prediction | Confidence | Inference time |
| --- | --- | ---: | ---: |
| `flattened-coca-cola-can...webp` | METAL | 98.44% | 851.221 ms |
| `360_F_774178590...jpg` | OTHER | 60.55% | 261.441 ms |

These are model measurements only; they do not authorize or represent a motor
or servo movement. The second result remains a low-confidence classification
and should be reviewed against its known material before training decisions.

## First physical two-image cycle

After the combined-test prerequisites were confirmed (600 effective steps per
carousel revolution, actuator authorization, clear mechanism, and emergency
cutoff), the guarded command ran on the Pi at `192.168.0.245`:

- Boot calibration: home detected after 49 steps.
- METAL image: stop 0 -> 2, 300 steps, position 12,072.698 ms, total 13,755.463 ms.
- OTHER image: stop 2 -> 3, 150 steps, position 6,040.958 ms, total 7,189.832 ms.
- Both cycles opened and closed the gate; all drivers stopped safely.

These are measured software/GPIO timings. The developer's physical observation
of the carousel stops and item drops must be recorded before M8 is marked fully
complete.

## Slow visible METAL recheck

At the developer's request, the Pi reran a slower visible sequence so the boot
calibration could be observed before the METAL move:

- Command target: Pi at `192.168.0.245`.
- Home search: 50 ms pulse delay, GPIO23 active-high IR home input.
- Boot calibration: home detected after 161 steps.
- Image: `flattened-coca-cola-can...webp`.
- Prediction: METAL, 98.44% confidence.
- Positioning: stop 0 -> 2, clockwise, 300 steps.
- Timing: prediction 558.370 ms, position 30,079.315 ms, gate open 500.259 ms, gate close 500.283 ms, total 31,638.312 ms.
- Cleanup: safe stop returned true.

These are the measured command results. The developer still needs to confirm
whether the visible calibration, METAL stop, and gate motion matched the
physical mechanism.
