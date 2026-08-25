# Changelog

All notable project changes are documented here.

## Unreleased

### Added

- Initial repository baseline and M0 environment audit documentation.
- M1 hardware inventory, wiring, and GPIO-map templates with safety gates.
- Updated M1 records with the confirmed Raspberry Pi, camera, sensors, NEMA17, DRV8825, MG995, touch switches, and provisional BCM assignments.
- Documented U1 as the fixed intake/camera trigger and U2-U5 as fixed fill stations mapped by calibrated carousel position.
- Added the M2 camera interface, Picamera2 adapter, deterministic mock, and capture documentation.
- Verified the real Pi OV5647 camera with the repository Picamera2 flow at 640x480; recorded one measured capture sample.
- Added M3 Kaggle bootstrap/remapping scripts, a transparent RGB-centroid baseline, and Pi-compatible offline inference.
- Downloaded Kaggle dataset version 1, remapped 4,752 images, and measured baseline holdout accuracy of 0.515; Pi deployment remains pending.
- Verified temporary Pi inference on a saved 640x480 JPEG: `OTHER`, score 0.318736, measured inference time 316.986 ms; temporary files removed.
- Added M4 hardware-independent U1 presence detection with ultrasonic mock, debouncing, and calibration documentation.
- Updated planning for TACO+Kaggle material mapping, two ultrasonic roles (U1 intake and U2 post-drop status), and active-low IR homing.
- Hardened TACO category remapping for plastic/metal/paper variants and added mapping tests.
