# M6 IR homing

Status: **M6 complete; physical homing verified with GPIO23 edge capture.**

The installed IR module is connected to BCM GPIO23 and has measured active-high
semantics:

- HIGH / approximately 3.3 V: carousel is at the mechanical 0-degree reference.
- LOW: carousel is away from the reference.

The homing policy samples GPIO23 before any movement and after every bounded
single-step pulse. If the input is already HIGH, it returns immediately without
energizing the motor. If the input never becomes HIGH, it stops after
`max_steps` and reports an error. The stepper adapter disables DRV8825 ENABLE
after every pulse and on all exits.

## Simulation and unit verification

`tests/unit/test_homing.py` covers already-home, movement-until-home, invalid
input, and the hard travel bound with a fake stepper and mock sensor. No GPIO
or actuator is used by these tests.

## Physical test (requires a fresh explicit confirmation)

```text
TEST: bounded IR homing toward the known home direction
HARDWARE: NEMA17 + DRV8825 + GPIO23 IR module
EXPECTED ACTION: if GPIO23 is LOW, the carousel moves at most max_steps one-step pulses and stops when GPIO23 becomes HIGH; if already HIGH, no movement
EXPECTED RESULT: JSON reports reached_home=true and a finite steps_taken; driver is disabled
STOP CONDITION: any vibration, binding, unexpected direction/travel, heat, smoke, sensor level disagreement, or emergency-cutoff issue
```

The command is intentionally locked and must include `--confirm-movement`:

```bash
PYTHONPATH=/home/ariyan/ai-trash-sorter-test/app \
/home/ariyan/.venvs/ai-trash-sorter/bin/python -m motors.home_test \
  --home-gpio 23 --direction 0 --max-steps 400 \
  --pulse-delay-ms 20 --confirm-movement
```

The `--direction` value is a mechanical installation property and must be
confirmed during the first homing test. This command must not be run while
adjusting VREF or while any person is inside the mechanism's travel area.

## First physical attempt

With developer authorization, the command was run once on the Pi using
`--direction 0`, `--max-steps 100`, and a 20 ms pulse delay. It stopped safely
with:

```json
{"error": "home not detected within 100 steps", "safe_off": true}
```

A subsequent read-only GPIO check returned level `0` (`is_home=false`). No
additional movement was attempted. Before retrying, verify the mechanical
direction toward the sensor, the sensor's physical alignment/clearance, and
GPIO23 wiring/polarity. Increase the travel bound only after those checks;
never bypass the bound.

## Slow one-revolution scan

At the developer's request, a second bounded test used 200 full steps in
`direction=0` with a 50 ms pulse delay (one nominal 360-degree revolution at
the configured full-step setting). GPIO23 never became HIGH:

```json
{"error": "home not detected within 200 steps", "safe_off": true}
```

The driver disabled safely. Do not keep repeating motor scans. Inspect the IR
module alignment/marker, its 3.3 V supply and ground, and GPIO23 continuity;
then perform a sensor-only level test before authorizing another movement.

## Timed search attempt

The authorized 90-second calibration search ran once with a 50 ms pulse delay,
`direction=0`, and a 2,000-step ceiling. It timed out without GPIO23 becoming
HIGH and shut the driver down safely:

```json
{"error": "home not detected within 90 seconds or 2000 steps", "safe_off": true}
```

This rules out only the earlier 100/200-step bound; it does not prove the
effective mechanical revolution count. Inspect the IR signal path and home
marker before any further actuator test.

The homing adapter now samples GPIO23 approximately every millisecond during
both phases of each STEP pulse and latches a HIGH edge, instead of reading only
once after a complete step. This handles a brief IR assertion as the marker
passes the sensor while retaining the time and step bounds.

## Successful edge-latched test

After deploying the edge-sampling fix to the Pi at `192.168.0.245`, the same
bounded command detected the brief home assertion:

```json
{"already_home": false, "direction": 0, "elapsed_ms": 16975.977, "home_gpio": 23, "reached_home": true, "safe_off": true, "steps_taken": 153}
```

The motor stopped at the detected home edge and the driver was disabled. The
153-step travel is a measured homing result, not yet a calibrated full-
revolution value.

## Timed calibration search

For mechanical calibration only, `motors.timed_home_test` provides a hard
90-second deadline plus a 2,000-step ceiling. It samples GPIO23 after each
bounded pulse and disables the driver on success, timeout, step limit, or
exception. This is not an unlimited homing loop.
