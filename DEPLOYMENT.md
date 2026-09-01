# Deployment

## Raspberry Pi Quick Automated Setup

Run the automated installer on the Raspberry Pi:

~~~bash
cd /path/to/Novi/raspberry-pi
sudo chmod +x setup.sh
sudo ./setup.sh
~~~

The installer configures `/opt/ai-trash-sorter`, sets up `.venv`, copies the model, configures `/etc/ai-trash-sorter/config.json`, and installs & enables the `ai-trash-sorter` systemd service for auto-starting on every Pi boot.

### Manual Step-by-Step Alternative:

1. Install Raspberry Pi OS camera support, picamera2, and lgpio.
2. Clone this repository at /opt/ai-trash-sorter.
3. Create `raspberry-pi/.venv`, activate it, and install `pip install -r raspberry-pi/requirements.txt`.
4. Copy `training/models/waste-mobilenet-taco-kaggle-v1.*` to `/opt/ai-trash-sorter/model/model.tflite` and `/opt/ai-trash-sorter/model/model.json`.
5. Copy `raspberry-pi/config.example.json` to `/etc/ai-trash-sorter/config.json`.
6. Put a Firebase service-account JSON in `/etc/ai-trash-sorter/firebase-service-account.json`.
7. Create `/var/lib/ai-trash-sorter`.
8. Enable the systemd service:
~~~bash
sudo install -m 644 raspberry-pi/systemd/ai-trash-sorter.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now ai-trash-sorter
journalctl -u ai-trash-sorter -f
~~~

## Firebase

Enable Realtime Database, Authentication with Email/Password, and Cloud Storage if event images must be viewable in Flutter. Use Firebase Authentication and Realtime Database rules to limit read/write access to authorized operators. The Pi service account must have only the required Realtime Database and Storage access.

Configure Flutter from novi_flutter_app:

~~~bash
dart pub global activate flutterfire_cli
flutterfire configure
flutter pub get
flutter run
~~~

FlutterFire creates platform Firebase settings; they are project identifiers, not a Pi service-account secret. Ensure deviceId in lib/main.dart matches the Pi configuration.

## Recovery

If the service logs homing or movement failure, leave the gate closed, clear the mechanism, correct the physical cause, and request homing from the app or restart the service. The Pi refuses normal movement while its position is unknown.
