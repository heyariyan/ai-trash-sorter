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
- Added M3 Kaggle bootstrap/remapping scripts and a MobileNetV2 transfer-learning trainer that exports a full-integer TFLite model with metadata.
- Retired the RGB-centroid baseline from both training and Pi runtime; no neural accuracy or Pi latency is claimed until the merged dataset is trained and measured.
- Added M4 hardware-independent U1 presence detection with ultrasonic mock, debouncing, and calibration documentation.
- Updated planning for TACO+Kaggle material mapping, two ultrasonic roles (U1 intake and U2 post-drop status), and active-high IR homing on GPIO23.
- Hardened TACO category remapping for plastic/metal/paper variants and added mapping tests.
- Added quantized TFLite inference with injectable interpreter tests and removed the former RGB runtime path.
- Added bounded TACO subset download, merged 4,831-image neural training run, and Pi test evaluation; one confirmed plastic sample remains misclassified and production deployment is blocked pending feedback retraining.
- Verified a live Pi camera capture followed by neural inference: 640x480 capture in 108.032 ms, `PLASTIC` at 92.19%, inference in 311.193 ms; ground truth was not recorded.
- Added the hardware-separated `LgpioStepper` DRV8825 adapter and completed one authorized 10-pulse movement test with safe-off cleanup; physical direction confirmation is pending.
- Recorded the authorized 10-second test result: the shaft moved briefly then vibrated, so further stepper tests are paused pending phase-wiring, current, supply, mechanical, and acceleration checks.
- Recorded the developer's successful follow-up stepper movement report and added bounded GPIO23 IR-home sensing/homing policy with simulation tests.
- Added calibrated four-stop bin positioning with shortest-path rotation and tests; servo drop sequencing remains in M7.
- Added a dual-bounded timed IR-home calibration command (deadline plus step ceiling); no unlimited actuator loop is permitted.
