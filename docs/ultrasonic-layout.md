# Ultrasonic sensor layout and bin mapping

Status: **Design decision for the five fixed sensors; physical placement still requires measurement.**

The sensors do not rotate with the carousel. Sensor names (`U1` through `U5`) therefore identify fixed physical stations, not permanent waste categories. The software must combine each reading with the stepper's calibrated position and the Hall home reference.

## Assignment

| Sensor | Fixed location | Purpose | When read |
| --- | --- | --- | --- |
| U1 | Insertion chute, before the camera view | Detect an item and activate the capture/classification workflow | Continuously or by a debounced polling loop while IDLE |
| U2 | Fill station A around the carousel | Measure the bin currently at station A | Only while the stepper is stopped |
| U3 | Fill station B around the carousel | Measure the bin currently at station B | Only while the stepper is stopped |
| U4 | Fill station C around the carousel | Measure the bin currently at station C | Only while the stepper is stopped |
| U5 | Fill station D around the carousel | Measure the bin currently at station D | Only while the stepper is stopped |

U1 is the camera trigger. U2-U5 are not camera triggers and do not directly mean BIODEGRADABLE, PLASTIC, METAL, or OTHER. They report the fill level of whichever physical bin is aligned with their station.

## Position-to-bin calculation

After homing, define:

```text
theta_machine = calibrated carousel angle relative to Hall home
bin_pitch     = 360 degrees / number_of_bins
bin_angle(i)  = (theta_machine + i * bin_pitch) modulo 360
```

For each fixed fill station `j`, store its measured angle `station_angle(j)`. A bin is considered aligned when the wrapped angular error is within a measured tolerance:

```text
error = abs(wrap_to_minus180_180(bin_angle(i) - station_angle(j)))
aligned if error <= alignment_tolerance
```

The event record stores the logical bin ID, the fixed station sensor, the stepper position, and the distance sample. This prevents a fixed sensor from being permanently associated with one category while the carousel rotates.

## Measurement policy

- Trigger only one ultrasonic sensor at a time to avoid acoustic cross-talk.
- Read fill sensors after the stepper has stopped and a mechanical settling delay has elapsed.
- Take several samples, reject timeouts/outliers, and use a median distance.
- Convert distance to a fill percentage only after measuring each bin's empty and full reference distances.
- If the carousel angle is not homed or a station is not aligned, mark the fill reading unknown rather than assigning it to a bin.
- Keep fill-level sensing out of the first offline sorting loop; it is a later feature once object detection and sorting are stable.

## Calibration required

Before enabling U2-U5 in software, measure and record:

1. Hall-home angle and step count.
2. Steps per revolution and selected DRV8825 microstep mode.
3. Each station angle and alignment tolerance.
4. Empty and full distance for every bin geometry.
5. Ultrasonic Echo voltage and the level-shifter/divider used.

No actuator movement or ultrasonic wiring is authorized from this document alone.
