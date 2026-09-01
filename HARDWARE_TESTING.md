# Hardware testing and safety

Do not run any real actuator command unless the carousel path, gate, and drop zone are clear, the mechanism can move without striking a person or object, and an emergency actuator-power disconnect is immediately available.

Before testing, verify:

- DRV8825 and MG995 use suitable external power; neither is powered from Pi GPIO.
- All grounds are common as required by the wiring design.
- Any HC-SR04-style Echo line is level-shifted to 3.3 V.
- IR home GPIO23 is active high at physical stop 0.
- GPIO18 servo endpoints are the actual calibrated values, not assumed angles.
- U1, U3, stepper direction, steps/revolution, and home maximum are configured in /etc/ai-trash-sorter/config.json.

## Sequence

1. With actuator power disconnected, run the Pi application enough to verify model loading, camera initialization, Firebase connection, and read-only sensor input.
2. Confirm the mechanism is clear and safe.
3. Enable actuator power and run the application under direct observation. Startup closes the gate, then performs bounded IR homing.
4. Verify startup reaches READY, stop 0 matches the mechanical home marker, and driver power is disabled after a move.
5. Place one test item beneath U1. Confirm capture, supported classification, shortest path, carousel arrival before gate open, gate close, then U3 measurement.
6. Test a two-stop path and verify it uses the configured deterministic tie direction.
7. Disconnect or obstruct the home sensor only under safe conditions to verify timeout: no unbounded movement and position remains unknown.
8. Submit correct and incorrect feedback through Flutter. Correct/expired images must disappear; incorrect images must appear in the corrected feedback category folder.

Never increase home_max_steps, servo endpoints, or movement speed based only on software output. Inspect the physical machine first.
