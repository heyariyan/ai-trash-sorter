# GPIO map

Status: **Proposed BCM map — not approved for physical wiring until voltage and continuity checks pass.**

The map below reserves I2C GPIO2/3 for the OLED if (and only if) the module is confirmed as I2C. It is a planning map, not permission to energize an actuator.

| Function | BCM GPIO | Physical pin | Direction / electrical behavior | Hardware confirmation |
| --- | --- | --- | --- | --- |
| Stepper STEP | 24 | 18 | Output; keep low at boot | DRV8825 carrier pinout required |
| Stepper DIR | 25 | 22 | Output; keep low at boot | DRV8825 carrier pinout required |
| Stepper ENABLE | 8 | 24 | Output; active-low, default safe-off | DRV8825 carrier pinout required |
| Stepper RESET | 7 | 26 | Output; hold disabled during startup | DRV8825 carrier pinout required |
| Stepper SLEEP | 9 | 21 | Output; hold disabled during startup | DRV8825 carrier pinout required |
| Servo signal | 18 | 12 | Hardware-PWM-capable output | MG995 supply and signal level required |
| Hall sensor | 23 | 16 | Input; level/polarity TBD | Module output check required |
| YES switch | 20 | 38 | Input; debounce and polarity TBD | Touch-module output check required |
| NO switch | 21 | 40 | Input; debounce and polarity TBD | Touch-module output check required |
| PREV switch | 16 | 36 | Input; debounce and polarity TBD | Touch-module output check required |
| NEXT switch | 12 | 32 | Input; debounce and polarity TBD | Touch-module output check required |
| OLED SDA (I2C) | 2 | 3 | I2C SDA; fixed pull-up present | OLED must be confirmed I2C |
| OLED SCL (I2C) | 3 | 5 | I2C SCL; fixed pull-up present | OLED must be confirmed I2C |
| Ultrasonic 1 TRIG/ECHO | 4 / 5 | 7 / 29 | Output / divided input | Sensor model and Echo level required |
| Ultrasonic 2 TRIG/ECHO | 17 / 6 | 11 / 31 | Output / divided input | Sensor model and Echo level required |
| Ultrasonic 3 TRIG/ECHO | 27 / 13 | 13 / 33 | Output / divided input | Sensor model and Echo level required |
| Ultrasonic 4 TRIG/ECHO | 22 / 19 | 15 / 35 | Output / divided input | Sensor model and Echo level required |
| Ultrasonic 5 TRIG/ECHO | 26 / 10 | 37 / 19 | Output / divided input | Sensor model and Echo level required |

The proposed map must be checked against the actual OLED interface, module pinouts, power rails, level shifting, current-limit setup, and emergency-stop plan before it becomes the approved map.
