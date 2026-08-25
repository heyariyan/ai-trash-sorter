# M7 MG995 servo gate

Status: **M7 complete; physical servo direction and open/close cycle verified by the developer.**

The MG995 signal is assigned to BCM GPIO18. The verified installation uses 50 Hz
`lgpio.tx_servo` pulses with reversed direction:

- 0 degrees -> 2500 microseconds
- 90 degrees -> 1500 microseconds

The driver defaults to this reversed mapping; `--normal-direction` is available
only for a different linkage. The original pulse limits and gate angles remain
configurable. The driver emits 50 Hz PWM with
configurable 500–2500 microsecond pulse limits. Closed/open angles and settling
time are configurable because the installed linkage must be calibrated without
driving into its mechanical stops.

`ServoGate` exposes only `open()` and `close()` to the sorter state machine.
`MockServo` covers the policy without energizing hardware. The first real test
must be one open/close cycle with servo power isolated from the Pi logic supply.

## Physical preflight required

- MG995 supply voltage and regulated current capacity confirmed.
- Servo ground common with Pi ground; servo power not taken from a GPIO pin.
- GPIO18 signal wiring confirmed and signal level compatible.
- Gate linkage travel limits and a manual power cutoff verified.
- Stepper power isolated or mechanism held safely during the servo test.
- Closed/open angles chosen conservatively; start away from hard stops.

The guarded command is:

```bash
PYTHONPATH=/home/ariyan/ai-trash-sorter-test/app \
/home/ariyan/.venvs/ai-trash-sorter/bin/python -m motors.servo_test \
  --signal-gpio 18 --closed-angle 0 --open-angle 90 \
  --settle-seconds 0.5 --confirm-movement
```

Expected result: one close, one open, one close, then PWM stop. Stop
immediately for binding, buzzing, overheating, unexpected travel, or a power
rail drop. Do not run this command until the preflight facts are confirmed.

## First physical command result

The guarded command was run once on the Pi at `192.168.0.245` with GPIO18,
closed angle 0 degrees, open angle 90 degrees, and 0.5 seconds settling. The
runtime returned:

```json
{"closed": true, "safe_stop": true}
```

This confirms the servo command completed and stopped safely. The developer
verified the physical direction and the 0-degree/90-degree gate travel.
