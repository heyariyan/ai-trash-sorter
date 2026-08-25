# Current state — M0 environment and repository audit

Audited on 2026-08-25 (Asia/Kolkata) from the developer PC workspace.

## Repository

- Workspace: `C:\Users\ariya\Desktop\Novi`
- Git branch: `main`
- Remote: `origin` → `https://github.com/heyariyan/ai-trash-sorter.git`
- Synchronization at this audit: local `main` equals `origin/main`; no uncommitted changes before this M0–M4 pass.
- Latest synchronized commit before this pass: `d3484b2 feat(ai): update material and sensor plan`.
- No force-push or destructive repository operation is permitted.

## Developer PC

| Capability | Result |
| --- | --- |
| Git | Installed and authenticated to the configured GitHub remote |
| Python | `uv` can provide a managed Python 3.12 environment for tests and tooling |
| Pillow / NumPy | Available through the test environment; required by camera/inference tooling |
| TensorFlow | Required on the training machine for M3 neural training; installation is checked by `train_neural.py` |
| Flutter / Android / Chrome | Outside M0–M4 scope; verify before the mobile milestone |

## Raspberry Pi

The connected Pi is a Raspberry Pi 3B+ running the camera capture path. The OV5647 camera was verified remotely over SSH with a real capture. Pi-side TFLite runtime availability and the final Python package versions must be checked before neural deployment; no actuator was moved.

## Confirmed hardware and revised roles

- Raspberry Pi Camera: M2 capture-only path verified.
- U1 ultrasonic: fixed intake/object-presence sensor and the only camera trigger.
- U2 ultrasonic: fixed post-drop bin-status sensor; sampled only after gate close and settling.
- IR home sensor: active-low semantics; HIGH = normal, LOW = 0° home.
- NEMA17 + DRV8825, MG995 gate servo, four touch switches, and OLED are planned runtime hardware. Exact electrical levels, OLED controller/interface, power supplies, and emergency cut-off remain validation gates before GPIO drivers or actuator tests.

## Milestone status

| Milestone | Status | Evidence |
| --- | --- | --- |
| M0 | Complete | This audit and repository boundary |
| M1 | Documentation complete; electrical verification pending | Hardware, wiring, and provisional BCM map |
| M2 | Complete | Warm camera abstraction, mock tests, and real Pi capture record |
| M3 | Neural model trained; test deployment only | 80.55% held-out accuracy; Pi evaluation in [model-evaluation.md](model-evaluation.md) |
| M4 | Simulation complete; GPIO validation pending | U1 debounced detector and tests |

The former RGB-centroid model is retired and is not a supported training or runtime path. No model accuracy or Pi inference latency is claimed until the neural model is trained and measured on the merged, owner-reviewed data.
