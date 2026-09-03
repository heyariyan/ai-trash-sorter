# 🗑️ Novi AI Smart Dustbin — Autonomous Edge Waste Sorter

[![License: MIT](https://img.shields.io/badge/License-MIT-emerald.svg)](LICENSE)
[![Platform: Raspberry Pi](https://img.shields.io/badge/Platform-Raspberry%20Pi%203B%2B%20%2F%204-red.svg)](https://www.raspberrypi.com/)
[![AI Engine: TFLite](https://img.shields.io/badge/AI-MobileNetV2%20TFLite-orange.svg)](https://www.tensorflow.org/lite)
[![Companion: Flutter](https://img.shields.io/badge/Companion%20App-Flutter%203.x-blue.svg)](https://flutter.dev)
[![Cloud: Firebase](https://img.shields.io/badge/Cloud-Firebase%20RTDB-amber.svg)](https://firebase.google.com)

**Novi** is an intelligent, autonomous edge robotic appliance that automatically detects, classifies, and sorts discarded waste into **4 distinct compartments** (`BIODEGRADABLE`, `PLASTIC`, `METAL`, `OTHER`). 

Powered by a **Raspberry Pi 3B+**, on-device **MobileNetV2 neural vision**, a 4-quadrant **stepper motor carousel**, an **MG995 servo drop gate**, an **SSD1306 OLED display**, and physical verification buttons — Novi operates safely in real-time with zero internet required for core sorting, while streaming live telemetry and analytics to a cross-platform **Flutter Web & Mobile dashboard**.

---

## 🌟 Key Features

* **🧠 On-Device AI Neural Vision**: Quantized MobileNetV2 image classifier running on the Pi CPU in **$\sim 80 - 150\text{ms}$** with zero cloud latency.
* **🛡️ 75% Confidence Safety Routing Rule**:
  * $\ge 75\%$ Confidence $\rightarrow$ Carousel rotates to the specific bin (`BIODEGRADABLE`, `PLASTIC`, `METAL`) and drops.
  * $< 75\%$ Confidence $\rightarrow$ Safely routed into the **`OTHER`** bin to prevent contamination of clean recyclable streams.
* **🔄 Shortest-Path Modular Stepper Carousel**: NEMA 17 stepper + DRV8825 with smooth **trapezoidal acceleration/deceleration ramping** ($50\text{ steps}/90^\circ$). Automatically plans the shortest clockwise or counter-clockwise path.
* **🔇 Jitter-Free MG995 Gate Servo**: Calibrated $90^\circ$ sweep with **automatic PWM Detach** on settle to eliminate idle buzzing, jitter, and motor heating.
* **👁️ Ultra-Fast Intake Detection**: Ultrasonic sensor trigger ($0 - 7\text{ cm}$) with digital debounce filtering.
* **🔘 Interactive 4-Button Physical Feedback**:
  * OLED prompts: `"<CATEGORY> correct? YES [20] / NO [21]"` for $8\text{ seconds}$.
  * Press **YES** to confirm.
  * Press **NO** to navigate categories with **PREV (Pin 16)** / **NEXT (Pin 12)** and save corrections.
  * Misclassified photos are **automatically saved locally** to `/var/lib/ai-trash-sorter/images/feedback/<CATEGORY>/` for continuous model retraining!
* **📱 Flutter Cross-Platform Companion App**:
  * Live 4-quadrant animated carousel visualizer.
  * Bin clearance gauges and ultrasonic depth telemetry.
  * Real-time sorting history capped to latest 10 events.
  * Remote homing calibration control.
* **📸 Built-in Web Dataset Collector**: Integrated web app (`dataset_collector.py`) streaming live 25 FPS video with 1-tap capture hotkeys for collecting custom training datasets in minutes.

---

## 🏗️ Hardware Architecture & Bill of Materials

| Component | Part / Model | Purpose / Details |
|---|---|---|
| **Main Controller** | **Raspberry Pi 3B+ / 4** | Edge compute, GPIO control, camera capture, neural inference |
| **Camera Module** | **Raspberry Pi Camera (OV5647)** | Top-down still capture ($640 \times 480$, $15\text{ms}$ memory grab) |
| **Carousel Stepper** | **NEMA 17 (17HS3401)** | 4-bin rotating carousel ($1.8^\circ/\text{step}$, $200\text{ steps/rev}$) |
| **Stepper Driver** | **DRV8825** | Microstepping driver with enable/sleep/reset logic |
| **Drop Gate Servo** | **MG995 Metal Gear Servo** | $90^\circ$ drop hatch mechanism on GPIO 18 |
| **Intake Sensor (U1)** | **HC-SR04 Ultrasonic** | Trigger sensor ($0 - 7\text{ cm}$ detection window) |
| **Bin Depth Sensor (U3)** | **HC-SR04 Ultrasonic** | Post-drop bin fill measurement |
| **Homing Sensor** | **A3144 Hall-Effect / IR Sensor** | $0^\circ$ Carousel home reference switch |
| **Status Display** | **SSD1306 OLED (128x64)** | I2C display (`0x3C`) for live prompts, meters & state |
| **Feedback Controls** | **4x Momentary Tactile Switches** | YES (20), NO (21), PREV (16), NEXT (12) buttons |
| **Power Supply** | **5V 3A (Pi) + 12V 2A (Stepper)** | Dedicated power rails for logic and motors |

---

## 🔌 Complete GPIO Pinout Table

| Hardware Component | Function | BCM GPIO | Physical Header Pin |
|---|---|---|---|
| **OLED Display** | I2C SDA | **GPIO 2** | **Pin 3** |
| **OLED Display** | I2C SCL | **GPIO 3** | **Pin 5** |
| **Ultrasonic U1 (Intake)** | Trigger | **GPIO 4** | **Pin 7** |
| **Ultrasonic U1 (Intake)** | Echo *(with 1k/2k divider)* | **GPIO 5** | **Pin 29** |
| **DRV8825 Stepper** | Reset (Active-Low) | **GPIO 7** | **Pin 26** |
| **DRV8825 Stepper** | Enable (Active-Low) | **GPIO 8** | **Pin 24** |
| **DRV8825 Stepper** | Sleep (Active-Low) | **GPIO 9** | **Pin 21** |
| **Button NEXT** | Navigation Input | **GPIO 12** | **Pin 32** |
| **Ultrasonic U3 (Bin)** | Echo *(with 1k/2k divider)* | **GPIO 13** | **Pin 33** |
| **Button PREV** | Navigation Input | **GPIO 16** | **Pin 36** |
| **Servo Gate (MG995)** | PWM Signal (50 Hz) | **GPIO 18** | **Pin 12** |
| **Button YES** | Confirm / Positive Feedback | **GPIO 20** | **Pin 38** |
| **Button NO** | Incorrect / Correction Entry | **GPIO 21** | **Pin 40** |
| **IR Home Sensor** | $0^\circ$ Home Reference | **GPIO 23** | **Pin 16** |
| **DRV8825 Stepper** | Step Pulse | **GPIO 24** | **Pin 18** |
| **DRV8825 Stepper** | Direction | **GPIO 25** | **Pin 22** |
| **Ultrasonic U3 (Bin)** | Trigger | **GPIO 27** | **Pin 13** |

> ⚠️ **Note on 5V Ultrasonic Echo**: The HC-SR04 Echo pin outputs $5\text{V}$, while the Raspberry Pi GPIO logic is $3.3\text{V}$. Always use a simple resistor voltage divider ($1\text{k}\Omega$ in series with Echo, $2\text{k}\Omega$ to GND) before connecting to the Pi GPIO.

---

## 🚀 Quick Start & Installation

### 1. Automated Raspberry Pi Setup
Clone this repository to your Raspberry Pi and run the automated installer:

```bash
git clone https://github.com/your-username/Novi.git
cd Novi/raspberry-pi
sudo chmod +x setup.sh
sudo ./setup.sh
```

The automated installer will:
1. Install system packages (`python3-picamera2`, `python3-lgpio`, `i2c-tools`, etc.).
2. Set up the Python virtual environment with dependencies (`luma.oled`, `Pillow`, `numpy`, `firebase-admin`, `ai-edge-litert`).
3. Generate `/etc/ai-trash-sorter/config.json`.
4. Install and enable the systemd service (`ai-trash-sorter.service`) to start on boot automatically.

### 2. Service Commands
```bash
# Start the smart bin
sudo systemctl start ai-trash-sorter

# View live real-time logs
sudo journalctl -u ai-trash-sorter -f

# Restart or Stop
sudo systemctl restart ai-trash-sorter
sudo systemctl stop ai-trash-sorter
```

---

## 📱 Flutter Mobile & Web Dashboard

The companion app is located in `novi_flutter_app/`.

### Run Locally:
```bash
cd novi_flutter_app
flutter pub get
flutter run -d chrome # or mobile device
```

### Deploy to Firebase Hosting:
```bash
cd novi_flutter_app
flutter build web --release
firebase deploy --only hosting
```

---

## 📸 Dataset Collector & AI Model Retraining

To collect photos from your smart bin camera and train a customized model:

### 1. Collect Real-World Photos on the Pi:
```bash
# Stop background sorter to free camera
sudo systemctl stop ai-trash-sorter

# Run web dataset collector
cd /opt/ai-trash-sorter/raspberry-pi
.venv/bin/python dataset_collector.py
```
Open **`http://<PI_IP>:8080`** on your phone/PC to view the live 25 FPS camera stream and tap buttons (or press physical switches on the Pi) to capture and label photos into `BIODEGRADABLE`, `PLASTIC`, `METAL`, `OTHER`.

### 2. Train and Export TFLite Model:
```bash
python training/scripts/train_neural.py
```
This trains a quantized MobileNetV2 model using heavy data augmentation and exports `model.tflite` directly to `training/models/`.

---

## 📂 Project Structure

```text
Novi/
├── docs/                        # Architecture, wiring, and deployment guides
├── novi_flutter_app/            # Flutter Web & Mobile Dashboard
│   ├── lib/
│   │   ├── models/              # Data models (SortingEvent, DeviceStatus)
│   │   ├── screens/             # Dashboard, History, Stats, Diagnostics, Settings
│   │   ├── services/            # Firebase Realtime DB & Auth service
│   │   ├── theme/               # Cyber-Eco design tokens & palettes
│   │   └── widgets/             # Gauges, visualizers, cards
│   └── web/                     # Web deployment entrypoint
├── raspberry-pi/                # Production Raspberry Pi Python Engine
│   ├── app/
│   │   ├── ai/                  # TFLite neural inference engine
│   │   ├── camera/              # Picamera2 in-memory streaming capture
│   │   ├── display/             # SSD1306 I2C OLED driver
│   │   ├── feedback/            # 4-Button physical input handler with debouncing
│   │   ├── motors/              # Stepper (DRV8825) & Servo (MG995 with PWM detach)
│   │   ├── object_detection/    # Ultrasonic debounced presence detector
│   │   ├── sensors/             # Ultrasonic (U1/U3) and IR homing drivers
│   │   ├── sorter/              # Autonomous state machine with 75% confidence rule
│   │   └── sorting/             # Shortest-path modular carousel positioning
│   ├── dataset_collector.py     # Live MJPEG dataset collector web tool
│   ├── setup.sh                 # Interactive automated Raspberry Pi installer
│   └── start.sh                 # Production execution script
└── training/                    # Machine Learning Pipeline
    ├── models/                  # Quantized .tflite weights & metadata
    └── scripts/                 # Training, dataset augmentation & export scripts
```

---

## 👥 Authors & Contributors

* **Ariyan Haque** ([@heyariyan](https://github.com/heyariyan)) — *Lead Creator, Embedded Systems, Hardware & Neural AI Architecture*
* **Ahan Ghosh** — *Hardware Design, Assembly & Testing Contributor*

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/heyariyan/ai-trash-sorter/issues).

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is open-source and licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<div align="center">
  <sub>Built with ❤️ for a cleaner, smarter, and more sustainable future.</sub>
</div>
