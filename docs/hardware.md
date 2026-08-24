# Hardware inventory

Status: **M1 blocked pending physical inventory confirmation.**

This document records only hardware that is actually present and identified. Do not infer a driver, display controller, power supply, or GPIO assignment from a component's appearance.

## Confirmed project hardware

| Component | Required role | Exact model / part number | Present? | Evidence / notes |
| --- | --- | --- | --- | --- |
| Raspberry Pi 3B+ | Main controller | TBD | Unknown | Photo or board serial required |
| Raspberry Pi Camera | Image capture | TBD | Unknown | Connector and camera revision required |
| Stepper motor | Sorter rotation | TBD | Unknown | Motor voltage/current and wire count required |
| Stepper driver | Stepper power/control | **REQUIRED** | Unknown | Model and pinout required before driver code |
| Servo motor | Drop gate | TBD | Unknown | Voltage/current and power source required |
| Hall-effect sensor | Mechanical home reference | TBD | Unknown | Digital/analog type and pull-up requirement required |
| YES switch | Feedback input | TBD | Unknown | Normally-open/closed and wiring required |
| NO switch | Feedback input | TBD | Unknown | Normally-open/closed and wiring required |
| PREV switch | Correction input | TBD | Unknown | Normally-open/closed and wiring required |
| NEXT switch | Correction input | TBD | Unknown | Normally-open/closed and wiring required |
| OLED | Status and prompts | **REQUIRED** | Unknown | Interface (I2C/SPI) and controller (for example SSD1306/SH1106) required |

## Required confirmation before GPIO work

Please provide a clear photo of each board label or the exact part number for:

1. The stepper motor driver, including its logic-voltage and motor-power requirements.
2. The OLED module, including controller and I2C/SPI interface.
3. The stepper motor and servo labels, if available.
4. The Raspberry Pi and camera module.

Also provide the intended power supplies, common-ground plan, mechanical travel limits, and an emergency way to remove actuator power. GPIO pin numbers will be assigned only after this information is verified.

## Safety gate

No motor or servo movement is authorized by this milestone. Until the inventory is complete, only inspection, mock tests, and simulation mode are allowed.
