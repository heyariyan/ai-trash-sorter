# AI Trash Sorter

An autonomous Raspberry Pi waste sorter. U1 detects an object closer than 7 cm, a warm camera captures it, the on-device TFLite model selects one of four bins, and the carousel uses its remembered position and the shortest rotational route to drop the item. The Pi works safely without the network or Flutter application.

The four configured classes are BIODEGRADABLE, PLASTIC, METAL, and OTHER; they may be changed only by changing both the model metadata and bin_order in the Pi configuration.

## Components

- Raspberry Pi: primary controller and sole owner of GPIO/motion.
- U1 ultrasonic: intake trigger (< 7 cm by default).
- Pi Camera: initialized once at startup and kept warm.
- TFLite model: loaded once at startup.
- DRV8825 + stepper: carousel movement, with active-high GPIO23 IR home reference.
- MG995 gate: GPIO18, calibrated values in configuration.
- U3 ultrasonic: post-drop bin distance.
- Optional SSD1306 and retained physical feedback controls.
- Firebase Realtime Database, Authentication, and optional Firebase Storage: operator interface only.

## Run the Pi application (Automated Setup)

On your Raspberry Pi, clone or copy this repository, then run the interactive installer:

~~~bash
cd Novi/raspberry-pi
sudo chmod +x setup.sh
sudo ./setup.sh
~~~

`setup.sh` will automatically:
1. Install all necessary Raspberry Pi OS packages (`picamera2`, `lgpio`, `i2c-tools`, etc.).
2. Set up the Python virtual environment and install dependencies.
3. Configure your Firebase Realtime Database URL and storage credentials.
4. Install and enable the systemd service (`ai-trash-sorter.service`) so the sorter starts automatically whenever the Raspberry Pi boots.

### Testing & Logs

- **Check live service logs**:
  ~~~bash
  sudo journalctl -u ai-trash-sorter -f
  ~~~
- **Run a non-actuating simulation smoke test**:
  ~~~bash
  cd /opt/ai-trash-sorter/raspberry-pi
  PYTHONPATH=app .venv/bin/python -m main --simulation --once
  ~~~
- **Restart / Stop service**:
  ~~~bash
  sudo systemctl restart ai-trash-sorter
  sudo systemctl stop ai-trash-sorter
  ~~~

## Images and correction feedback

Each successful capture starts in /var/lib/ai-trash-sorter/images/temp/<event-id>.jpg. It is temporary; the Pi asynchronously watches Firebase feedback by that exact event ID.

- “AI was correct”, or expiry of temporary_image_ttl_seconds: local and optional Firebase Storage temporary copies are deleted.
- “Prediction incorrect” + corrected category: the Pi moves the image into /var/lib/ai-trash-sorter/images/feedback/<CATEGORY>/ and marks the Firebase event corrected.

The physical cycle never waits for feedback. Cloud Storage is optional but enables the Flutter app to show a temporary or retained image during its bounded retention period.

## Flutter operator app

The application in [novi_flutter_app](novi_flutter_app) authenticates users with Firebase Authentication and reads the Pi’s Realtime Database state. It can request homing and submit event-scoped feedback; it contains no GPIO or motor control.

Run flutterfire configure from novi_flutter_app for the target Firebase project, then flutter pub get and flutter run. Firebase’s setup flow creates the platform configuration required by the app. See [DEPLOYMENT.md](DEPLOYMENT.md).

## Documentation

- [Architecture](ARCHITECTURE.md)
- [Deployment](DEPLOYMENT.md)
- [Hardware safety and verification](HARDWARE_TESTING.md)
