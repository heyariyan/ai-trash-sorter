# AI Trash Sorter

AI Trash Sorter is a local-first, Raspberry Pi-powered waste-sorting appliance. It captures an item, classifies it as `BIODEGRADABLE`, `PLASTIC`, `METAL`, or `OTHER`, routes it mechanically, and records the result locally.

The physical sorting loop is designed to work entirely offline. Remote access and the Flutter companion app are optional clients, not dependencies of the appliance.

## Project status

M0 repository audit is complete. M1 hardware documentation and the provisional
GPIO plan are complete, with electrical validation still required. M2 camera
capture and real Pi verification are complete. M3 now uses a MobileNetV2 neural
training/export path and quantized TFLite runtime; a production model awaits
training and measured Pi evaluation. M4 U1 presence detection is implemented
in simulation. No motor-control code or physical actuator test has been
created or performed.

## Safety

Set `AI_TRASH_SORTER_SIMULATION=true` for all early end-to-end runs. Real motor movement requires explicit human confirmation after the driver model, wiring, power, GPIO assignments, mechanical limits, and emergency power-cut procedure are verified.

## Repository layout

The target layout and deployment boundaries are documented in [docs/current-state.md](docs/current-state.md). Source directories will be added one bounded milestone at a time.

## License

The project is released under the MIT License in [LICENSE](LICENSE).
