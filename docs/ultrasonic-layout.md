# Ultrasonic sensor layout and bin-status plan

Status: **Runtime plan implemented for two fixed ultrasonic sensors; physical GPIO validation still required before a real loop run.**

The project now uses two ultrasonic sensors only. Sensor identity is fixed by its physical role, while the logical bin identity comes from the stepper position and selected bin.

## Assignment

| Sensor | Fixed location | Purpose | When read |
| --- | --- | --- | --- |
| U1 | Insertion chute, before the camera view | Detect an item and start the camera/classification workflow | Debounced polling while IDLE |
| U3 | Post-drop bin-status position | Measure the selected bin after the trash has been loaded | After gate close and mechanical settling |

U1 is the only camera trigger. U3 is the only bin-status sensor in the current runtime. U3 does not classify the item and does not replace the AI prediction; it records a distance/fill observation associated with the selected logical bin.

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
  -> trigger U3 and take validated samples
  -> save selected_bin + U3 distance/fill observation
  -> return home / READY
```

U3 must not be sampled while the gate is open, while the item is falling, or while the stepper is moving. Those conditions can produce a false fill reading.

## Position-to-bin association

U3 is fixed, so its sensor number is not a permanent material category. The event must store the selected logical bin and the calibrated stepper position at the time of the U3 read:

```text
selected_bin = decision selected by the AI
carousel_angle = calibrated stepper angle after homing
u3_distance_cm = post-drop distance observation
```

If the mechanism requires the selected bin to move to a separate U3 inspection position, the state machine must perform that move before sampling and record the final angle. If the drop position and U3 position are the same, no additional movement is required.

## Measurement and dataset record

For each completed drop, record:

- `event_id` and timestamp
- predicted category and confidence
- `selected_bin`
- calibrated stepper angle/position
- U3 distance sample and any later median/filtered distance
- empty/full calibration values and derived fill percentage, when calibrated
- sensor timeout/invalid status

U3 observations become training metadata and bin-status data. They must not silently overwrite the visual label.

## Calibration and physical gate

Before enabling U3 in a physical loop, measure and record:

1. Empty-bin and full-bin distances at the U3 mounting position.
2. A valid distance range and timeout behavior.
3. The settling delay after gate close.
4. Ultrasonic Echo voltage and the verified divider/level shifter.
5. Whether the selected bin is already under U3 after dropping or needs a separate position.

No actuator movement or ultrasonic wiring is authorized from this document alone.
