# Intelligent four-bin positioning

The carousel is calibrated at startup by homing against GPIO23. A HIGH IR
input establishes mechanical 0 degrees as logical stop `0`. The default stop
mapping is:

| Stop | Category | Angle |
| ---: | --- | ---: |
| 0 | BIODEGRADABLE | 0 degrees |
| 1 | PLASTIC | 90 degrees |
| 2 | METAL | 180 degrees |
| 3 | OTHER | 270 degrees |

The mapping and calibrated full-revolution step count are configuration values;
the software does not assume that every installation has exactly 200 effective
steps per revolution.

After homing, the position controller calculates a modular shortest path. For
example, from BIODEGRADABLE (stop 0) to OTHER (stop 3), it commands one reverse
stop (50 steps at the default 200-step/revolution setting), not three forward
stops (150 steps). The current logical position is updated only after the
stepper call succeeds; after an interruption it is invalidated and must be
re-homed.

This layer only selects and positions the bin. Camera/AI classification supplies
the category, and the servo gate/drop sequence will be added in the servo
milestone. No physical movement is started by the planner or its tests.
