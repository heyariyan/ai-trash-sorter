# Hardware inventory

Status: **M1 partially confirmed; electrical details and OLED identification remain open.**

This document records only hardware that is actually present and identified. Do not infer a driver, display controller, power supply, or GPIO assignment from a component's appearance.

## Confirmed project hardware

| Component | Required role | Exact model / part number | Present? | Evidence / notes |
| --- | --- | --- | --- | --- |
| Raspberry Pi 3B+ | Main controller | Raspberry Pi 3 Model B+ | Yes | Confirmed by developer |
| Raspberry Pi Camera | Image capture | Exact revision TBD | Yes | Confirm camera connector/module revision |
| Ultrasonic sensor U1 | Intake/object detection and camera trigger | Exact model TBD | Yes | Confirm whether HC-SR04 or 3.3 V-compatible variant |
| Ultrasonic sensor U2 | Post-drop bin-status measurement | Exact model TBD | Yes | Confirm whether HC-SR04 or 3.3 V-compatible variant |
| NEMA17 stepper motor | Sorter rotation | NEMA17 | Yes | Coil pairs and DRV8825 wiring verified by developer; rated phase current should remain documented |
| Stepper driver | Stepper power/control | DRV8825 carrier | Yes | VMOT 12 V; VREF 0.63 V; stated current limit approximately 1.26 A; M0/M1/M2 at GND (full-step) |
| Servo motor | Drop gate | MG995 | Yes | Signal GPIO18 confirmed; use a separate regulated supply and confirm voltage/current/endpoints before movement |
| IR home sensor module | Mechanical home reference | Exact module/output TBD | Yes | GPIO23; HIGH/3.3 V = home/0 degrees, LOW = away from home |
| YES switch | Feedback input | Touch module; exact model TBD | Yes | Confirm output voltage and active polarity |
| NO switch | Feedback input | Touch module; exact model TBD | Yes | Confirm output voltage and active polarity |
| PREV switch | Correction input | Touch module; exact model TBD | Yes | Confirm output voltage and active polarity |
| NEXT switch | Correction input | Touch module; exact model TBD | Yes | Confirm output voltage and active polarity |
| OLED | Status and prompts | **REQUIRED** | Yes | Interface (I2C/SPI) and controller (for example SSD1306/SH1106) still unknown |

## Required confirmation before GPIO work

Please provide a clear photo of each board label or the exact part number for:

1. The DRV8825 carrier board, including its logic-voltage, motor-power, current-limit, and pin labels.
2. The OLED module, including controller and I2C/SPI interface.
3. The two ultrasonic sensor models and whether their Echo outputs are 3.3 V or 5 V.
4. The IR home sensor output voltage and active-high behavior are recorded as 3.3 V HIGH at home.
5. The touch-module output voltage/polarity.
6. The stepper motor and servo labels, if available.

Also provide the intended power supplies, common-ground plan, mechanical travel limits, and an emergency way to remove actuator power. GPIO pin numbers will be assigned only after this information is verified.

## Safety gate

The M1 inventory gate is historical. M5 stepper movement has since been
authorized and reported successful. M6 homing remains bounded and locked behind
an explicit confirmation; no homing movement is started by documentation or
unit tests.
