# Current state — M0 environment and repository audit

Audited on 2026-08-24 (Asia/Kolkata) from the developer PC workspace.

## Repository

- Workspace: `C:\Users\ariya\Desktop\Novi`
- Starting state: empty directory; it was not a Git repository.
- Git repository: initialized locally on branch `main`.
- Git remote: none configured, so no GitHub push is possible yet.
- Existing Git identity: `heyariyan <thisisariyanhaque@gmail.com>`.
- No existing project code was found or overwritten.

## Developer PC

| Capability | Result |
| --- | --- |
| Git | Installed: `2.52.0.windows.1` |
| VS Code | Installed and on `PATH` |
| Flutter / Dart | Installed on `PATH`; detailed version/doctor check did not complete during this audit |
| Python | `python` resolves to a Windows Store alias but cannot execute; a real Python installation is required for training and Pi tooling |
| Java / Android `adb` | Not found on `PATH`; Android toolchain remains unverified |
| Chrome | Not verified on `PATH` |
| GitHub CLI | Not found |

## Raspberry Pi

No Pi hostname, IP address, SSH configuration, or physical connection was supplied. The Pi OS, Python version, camera availability, storage, and network configuration are therefore unverified.

## Hardware

The developer confirmed a Raspberry Pi 3B+, Raspberry Pi Camera, five ultrasonic sensors (4+1), MG995 servo, NEMA17 stepper, DRV8825 stepper driver, Hall-effect sensor module, four touch switches, and an OLED. The ultrasonic, Hall, touch, and OLED module variants and electrical levels are still unverified. GPIO code must not be written until those details and wiring are checked.

## Planned repository and deployment boundaries

The project will be built incrementally toward this layout:

```text
raspberry-pi/       Pi runtime subset: app, provisioning, model, config, services
mobile/flutter_app/ Companion client only; never runs sorting logic
pocketbase/         Schemas, migrations, and hooks only; no live database data
cloudflare/         Tunnel templates and documentation only
training/           Developer-machine-only dataset tooling and experiments
tests/              Unit and integration tests
scripts/            Pi deployment, backup, restore, and diagnostics scripts
docs/               Architecture, hardware, setup, testing, and operations documentation
```

The deployed Pi will eventually use `/opt/ai-trash-sorter/` for application files, `/var/lib/ai-trash-sorter/` for runtime data, and `/etc/ai-trash-sorter/` for device configuration and secrets. These paths have not been created or modified.

## M0 outcome

M0 is complete. M1 documentation and a provisional BCM GPIO map have been added. M1 remains blocked pending the DRV8825 carrier-board pinout/current-limit details, OLED interface/controller, sensor output voltages, power supplies, and continuity-tested wiring.
