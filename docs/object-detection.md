# M4 object detection

Status: **Simulation and debounced detector implemented; U1 GPIO wiring remains pending electrical validation.**

## U1 role

U1 is the fixed ultrasonic sensor at the insertion chute. It detects that an item is present and triggers the later camera workflow. U2-U5 remain fill-level sensors and are not part of this milestone.

## Software boundary

`ObjectPresenceDetector` consumes the `UltrasonicSensor` interface and returns a debounced `PresenceReading`. It contains no GPIO, camera, motor, servo, network, or database code.

- `MockUltrasonicSensor` provides deterministic simulation and tests.
- Invalid readings and timeouts preserve the last safe state and are marked `valid=false`.
- Presence and clear transitions require consecutive samples, preventing one noisy reading from starting a capture.
- `present_threshold_cm` is deliberately configurable and must be measured at the installed U1 geometry.

## Calibration and physical gate

Before adding a GPIO implementation, confirm the exact ultrasonic module and Echo voltage. If Echo is 5 V, use a verified divider or level shifter. With motors disabled, measure:

1. Empty-chute distance.
2. Nearest expected item distance.
3. A threshold with margin between those distributions.
4. Sensor timeout behavior and maximum polling rate.

Only after those readings are recorded may a real U1 adapter be added. The first hardware test must be sensor-read-only and must not start the camera or move an actuator.
