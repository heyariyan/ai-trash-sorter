# Wiring plan

Status: **M1 blocked pending hardware identification.**

This is a planning document, not a wiring instruction. Pin numbers and connections marked `TBD` must not be connected or driven.

## Connection groups

```text
Raspberry Pi 3B+
  +-- camera connector ---------------- Raspberry Pi Camera (TBD)
  +-- GPIO ---------------------------- Hall sensor (TBD)
  +-- GPIO ---------------------------- YES / NO / PREV / NEXT switches (TBD)
  +-- GPIO ---------------------------- stepper driver logic (TBD)
  +-- GPIO/PWM ------------------------ servo signal (TBD)
  +-- I2C or SPI ---------------------- OLED (TBD)

Separate actuator supply ------------- stepper driver motor power (TBD)
Separate regulated servo supply ------- servo power (TBD)
Pi ground and signal grounds ----------- common-ground decision (TBD)
```

## Rules

- Never power a stepper motor or servo from a Raspberry Pi GPIO pin.
- Confirm the driver's logic voltage is Pi-compatible before connecting a GPIO signal.
- Confirm a common ground between the Pi and each externally powered driver.
- Add appropriate pull-up or pull-down resistors only after the Hall sensor and switch electrical behavior is known.
- Keep actuator power disabled while checking continuity and GPIO levels.
- Do not connect or energize the circuit from this document until the inventory table is complete and reviewed.

## Missing information

The exact stepper driver model, OLED controller/interface, motor and servo supply ratings, sensor type, switch wiring, and physical pin plan are still unknown.
