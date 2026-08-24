# AI Trash Sorter

AI Trash Sorter is a local-first, Raspberry Pi-powered waste-sorting appliance. It captures an item, classifies it as `BIODEGRADABLE`, `PLASTIC`, `METAL`, or `OTHER`, routes it mechanically, and records the result locally.

The physical sorting loop is designed to work entirely offline. Remote access and the Flutter companion app are optional clients, not dependencies of the appliance.

## Project status

Milestones M0 and M1 documentation are complete. M2 camera capture and real Pi verification are complete. M3 v0 baseline training and temporary Pi inference are complete; M4 simulation presence detection is implemented. The baseline is not production quality, and no motor-control code or physical actuator test has been created or performed.

## Safety

Set `AI_TRASH_SORTER_SIMULATION=true` for all early end-to-end runs. Real motor movement requires explicit human confirmation after the driver model, wiring, power, GPIO assignments, mechanical limits, and emergency power-cut procedure are verified.

## Repository layout

The target layout and deployment boundaries are documented in [docs/current-state.md](docs/current-state.md). Source directories will be added one bounded milestone at a time.

## License

The project is released under the MIT License in [LICENSE](LICENSE).
