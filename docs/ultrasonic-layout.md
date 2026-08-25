# Ultrasonic sensor layout and bin-status plan

Status: **Planning update: two fixed ultrasonic sensors; physical placement and electrical levels still require validation.**

The project now uses two ultrasonic sensors only. Sensor identity is fixed by its physical role, while the logical bin identity comes from the stepper position and selected bin.

## Assignment

| Sensor | Fixed location | Purpose | When read |
| --- | --- | --- | --- |
| U1 | Insertion chute, before the camera view | Detect an item and start the camera/classification workflow | Debounced polling while IDLE |
| U2 | Post-drop bin-status position | Measure the selected bin after the trash has been loaded | After gate close and mechanical settling |

U1 is the only camera trigger. U2 is the only bin-status sensor. U2 does not classify the item and does not replace the AI prediction; it records a distance/fill observation associated with the selected logical bin.

## Sorting-cycle sequence

```text
U1 detects item
  -> capture image
  -> classify item
  -> move selected bin to drop position
  -> open gate
  -> item drops
  -> close gate
  -> wait for mechanical settling
  -> trigger U2 and take validated samples
  -> save selected_bin + U2 distance/fill observation
  -> return home / READY
```

U2 must not be sampled while the gate is open, while the item is falling, or while the stepper is moving. Those conditions can produce a false fill reading.

## Position-to-bin association

U2 is fixed, so its sensor number is not a permanent material category. The event must store the selected logical bin and the calibrated stepper position at the time of the U2 read:

```text
selected_bin = decision selected by the AI
carousel_angle = calibrated stepper angle after homing
u2_distance_cm = median of valid post-drop samples
```

If the mechanism requires the selected bin to move to a separate U2 inspection position, the state machine must perform that move before sampling and record the final angle. If the drop position and U2 position are the same, no additional movement is required.

## Measurement and dataset record

For each completed drop, record:

- `event_id` and timestamp
- predicted category and confidence
- `selected_bin`
- calibrated stepper angle/position
- U2 distance samples and median distance
- empty/full calibration values and derived fill percentage, when calibrated
- sensor timeout/invalid status

U2 observations become training metadata and bin-status data. They must not silently overwrite the visual label.

## Calibration and physical gate

Before enabling U2 in software, measure and record:

1. Empty-bin and full-bin distances at the U2 mounting position.
2. A valid distance range and timeout behavior.
3. The settling delay after gate close.
4. Ultrasonic Echo voltage and the verified divider/level shifter.
5. Whether the selected bin is already under U2 after dropping or needs a separate position.

No actuator movement or ultrasonic wiring is authorized from this document alone.
