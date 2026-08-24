# GPIO map

Status: **TBD — no GPIO assignments are approved.**

The map below is intentionally unassigned. It prevents code and wiring from silently selecting pins before the hardware inventory and electrical checks are complete.

| Function | BCM GPIO | Physical pin | Direction / electrical behavior | Hardware confirmation |
| --- | --- | --- | --- | --- |
| Stepper STEP | TBD | TBD | TBD | Driver model required |
| Stepper DIR | TBD | TBD | TBD | Driver model required |
| Stepper ENABLE | TBD | TBD | TBD | Driver model required |
| Servo signal | TBD | TBD | PWM output | Servo voltage/power required |
| Hall sensor | TBD | TBD | Input; pull-up/down TBD | Sensor type required |
| YES switch | TBD | TBD | Input; debounce TBD | Switch wiring required |
| NO switch | TBD | TBD | Input; debounce TBD | Switch wiring required |
| PREV switch | TBD | TBD | Input; debounce TBD | Switch wiring required |
| NEXT switch | TBD | TBD | Input; debounce TBD | Switch wiring required |
| OLED SDA/MOSI | TBD | TBD | I2C/SPI TBD | Controller/interface required |
| OLED SCL/SCLK | TBD | TBD | I2C/SPI TBD | Controller/interface required |
| OLED CS/DC/RST | TBD | TBD | SPI-only lines, if applicable | Controller/interface required |

Assignments will be made only after the hardware inventory is confirmed, checked against Raspberry Pi 3B+ reserved pins, and documented with the power and emergency-stop plan.
