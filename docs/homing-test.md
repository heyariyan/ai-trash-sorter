# M6 IR homing

Status: **Software and simulation complete; physical homing verification is pending.**

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
