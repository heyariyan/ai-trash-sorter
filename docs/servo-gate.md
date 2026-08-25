# M7 MG995 servo gate

Status: **Software and simulation complete; physical servo test pending.**

The MG995 signal is assigned to BCM GPIO18. The driver emits 50 Hz PWM with
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
  --signal-gpio 18 --closed-angle 15 --open-angle 75 \
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

This confirms the PWM command completed and stopped safely. The developer's
physical observation of the gate travel must be recorded before M7 is marked
fully complete.
