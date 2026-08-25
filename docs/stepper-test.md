# M5 DRV8825 stepper test

Status: **Initial authorized movement test completed; physical direction confirmation pending.**

## Preflight confirmation

- DRV8825 carrier verified.
- VMOT: 12 V.
- Current limit: 1.5 A.
- Pi/driver common ground: verified.
- NEMA17 coil pairs: verified.
- STEP/DIR/ENABLE/RESET/SLEEP BCM wiring: verified.
- Mechanical limits and emergency cutoff: verified by developer.
- Servo power: isolated.
- IR home sensor: intentionally not used in M5; reserved for M6 homing.

## Test performed

```text
TEST: 10 STEP pulses, DIR=LOW, 5 ms high/low pulse delay
HARDWARE: NEMA17 + DRV8825 at 12 V / 1.5 A
EXPECTED ACTION: one short movement in the DIR=LOW direction
STOP CONDITION: any binding, grinding, heat, smoke, unexpected travel, or loss of cutoff
SAFE EXIT: ENABLE high, STEP low, RESET low, SLEEP low
```

The repository `LgpioStepper` adapter was copied to the Pi test directory and
ran once through `motors.stepper_test`. The Pi returned:

```json
{"direction": 0, "elapsed_ms": 297.707, "pulse_delay_ms": 5.0, "safe_off": true, "steps": 10}
```

No servo, IR sensor, camera, or sorter state machine was started.

## Developer confirmation required

Please confirm whether the shaft moved in the expected direction, moved the
expected amount, and remained mechanically quiet/cool. No second movement or
direction-reversal test should run until that observation is recorded.
