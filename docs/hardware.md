# Hardware inventory

Status: **M1 partially confirmed; electrical details and OLED identification remain open.**

This document records only hardware that is actually present and identified. Do not infer a driver, display controller, power supply, or GPIO assignment from a component's appearance.

## Confirmed project hardware

| Component | Required role | Exact model / part number | Present? | Evidence / notes |
| --- | --- | --- | --- | --- |
| Raspberry Pi 3B+ | Main controller | Raspberry Pi 3 Model B+ | Yes | Confirmed by developer |
| Raspberry Pi Camera | Image capture | Exact revision TBD | Yes | Confirm camera connector/module revision |
| Ultrasonic sensors (4+1) | Object/fill sensing | Exact model TBD | Yes | Confirm whether HC-SR04 or 3.3 V-compatible variant |
| NEMA17 stepper motor | Sorter rotation | Exact coil rating TBD | Yes | Confirm rated current and wire count |
| Stepper driver | Stepper power/control | DRV8825 | Yes | This is a stepper driver, not a servo driver; confirm carrier-board variant |
| Servo motor | Drop gate | MG995 | Yes | Use a separate regulated servo supply; confirm voltage/current rating |
| Hall-effect sensor module | Mechanical home reference | Exact module/output TBD | Yes | Confirm output voltage and active polarity |
| YES switch | Feedback input | Touch module; exact model TBD | Yes | Confirm output voltage and active polarity |
| NO switch | Feedback input | Touch module; exact model TBD | Yes | Confirm output voltage and active polarity |
| PREV switch | Correction input | Touch module; exact model TBD | Yes | Confirm output voltage and active polarity |
| NEXT switch | Correction input | Touch module; exact model TBD | Yes | Confirm output voltage and active polarity |
| OLED | Status and prompts | **REQUIRED** | Yes | Interface (I2C/SPI) and controller (for example SSD1306/SH1106) still unknown |

## Required confirmation before GPIO work

Please provide a clear photo of each board label or the exact part number for:

1. The DRV8825 carrier board, including its logic-voltage, motor-power, current-limit, and pin labels.
2. The OLED module, including controller and I2C/SPI interface.
3. The ultrasonic sensor model and whether its Echo output is 3.3 V or 5 V.
4. The Hall and touch-module output voltage/polarity.
5. The stepper motor and servo labels, if available.

Also provide the intended power supplies, common-ground plan, mechanical travel limits, and an emergency way to remove actuator power. GPIO pin numbers will be assigned only after this information is verified.

## Safety gate

No motor or servo movement is authorized by this milestone. Until the electrical inventory is complete, only inspection, mock tests, and simulation mode are allowed.
