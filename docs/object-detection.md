# M4 object detection

Status: **Debounced detector and GPIO ultrasonic adapter implemented; U1 physical read-only validation still required.**

## U1 role

U1 is the fixed ultrasonic sensor at the insertion chute. It detects that an item is present and triggers the later camera workflow when the item is within the configured 7 cm threshold. U3 is reserved for the post-drop bin-status measurement and is not part of this trigger detector.

The active-high IR home sensor on GPIO23 is a separate mechanical reference
(HIGH/3.3 V = 0° home, LOW = not home). It is not used as an object trigger and is intentionally
not coupled to this detector.

## Software boundary

`ObjectPresenceDetector` consumes the `UltrasonicSensor` interface and returns a debounced `PresenceReading`. It contains no GPIO, camera, motor, servo, network, or database code.

- `MockUltrasonicSensor` provides deterministic simulation and tests.
- `LgpioUltrasonicSensor` provides the real GPIO trigger/echo adapter once Echo voltage protection is verified.
- Invalid readings and timeouts preserve the last safe state and are marked `valid=false`.
- Presence and clear transitions require consecutive samples, preventing one noisy reading from starting a capture.
- `present_threshold_cm` is deliberately configurable and must be measured at the installed U1 geometry.

## Calibration and physical gate

Before adding a GPIO implementation, confirm the exact ultrasonic module and Echo voltage. If Echo is 5 V, use a verified divider or level shifter. With motors disabled, measure:

1. Empty-chute distance.
2. Nearest expected item distance.
3. A threshold with margin between those distributions.
4. Sensor timeout behavior and maximum polling rate.

The first hardware validation must be sensor-read-only and must not start the camera or move an actuator. U3 must be sampled only after gate close and mechanical settling.
