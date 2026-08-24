# Wiring plan

Status: **M1 partially confirmed; verify module electrical levels before wiring.**

This is a planning document, not a wiring instruction. Pin numbers and connections marked `TBD` must not be connected or driven.

## Connection groups

```text
Raspberry Pi 3B+
  +-- camera connector ---------------- Raspberry Pi Camera
  +-- GPIO ---------------------------- Hall sensor module (level check first)
  +-- GPIO ---------------------------- four touch switches (level check first)
  +-- GPIO ---------------------------- DRV8825 STEP/DIR/ENABLE/RESET/SLEEP
  +-- GPIO/PWM ------------------------ MG995 servo signal
  +-- I2C (proposed) ------------------ OLED (controller/interface confirmation required)
  +-- GPIO ---------------------------- five ultrasonic TRIG/ECHO pairs

Separate motor supply ----------------- DRV8825 VMOT and NEMA17
Separate regulated servo supply ------- MG995 power
Pi ground and signal grounds ----------- common ground after electrical review
```

## Rules

- Never power a stepper motor or servo from a Raspberry Pi GPIO pin.
- Confirm the driver's logic voltage is Pi-compatible before connecting a GPIO signal.
- Keep DRV8825 motor voltage (VMOT) separate from the Pi logic supply; set the current limit before connecting the NEMA17.
- Keep DRV8825 RESET and SLEEP in their disabled state during wiring and startup checks.
- Ultrasonic Echo lines must be level-shifted or divided if the selected sensor drives 5 V; Pi GPIO inputs are 3.3 V only.
- MG995 power must come from a regulated supply sized for its stall current, with grounds commoned to the Pi signal ground.
- Confirm a common ground between the Pi and each externally powered driver.
- Add appropriate pull-up or pull-down resistors only after the Hall sensor and switch electrical behavior is known.
- Keep actuator power disabled while checking continuity and GPIO levels.
- Do not connect or energize the circuit from this document until the inventory table is complete and reviewed.

## Missing information

The OLED controller/interface, motor and servo supply ratings, sensor output levels, switch polarity, and final continuity-tested wiring are still unknown.
