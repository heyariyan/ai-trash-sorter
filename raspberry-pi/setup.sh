#!/bin/bash
# =============================================================================
# Novi AI Trash Sorter - Raspberry Pi Automated Installer & Service Setup
# =============================================================================
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}=====================================================${NC}"
echo -e "${GREEN}     Novi AI Trash Sorter - Raspberry Pi Setup       ${NC}"
echo -e "${BLUE}=====================================================${NC}"

if [ "$(id -u)" -ne 0 ]; then
  echo -e "${RED}Error: Please run setup.sh with sudo:${NC}"
  echo "  sudo ./setup.sh"
  exit 1
fi

REAL_USER="${SUDO_USER:-$(logname 2>/dev/null || echo "$USER")}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
INSTALL_DIR="/opt/ai-trash-sorter"
CONFIG_DIR="/etc/ai-trash-sorter"
DATA_DIR="/var/lib/ai-trash-sorter"

# ── Stop & remove any existing service ──
echo -e "\n${YELLOW}[0/7] Stopping any existing ai-trash-sorter service...${NC}"
if systemctl is-active --quiet ai-trash-sorter 2>/dev/null; then
  systemctl stop ai-trash-sorter
  echo -e "${GREEN}  Service stopped.${NC}"
fi
if systemctl is-enabled --quiet ai-trash-sorter 2>/dev/null; then
  systemctl disable ai-trash-sorter 2>/dev/null || true
  echo -e "${GREEN}  Service disabled.${NC}"
fi
rm -f /etc/systemd/system/ai-trash-sorter.service 2>/dev/null || true
systemctl daemon-reload 2>/dev/null || true
echo -e "${GREEN}  Old service removed.${NC}"

# ── Install system packages ──
echo -e "\n${YELLOW}[1/7] Installing Raspberry Pi OS system packages...${NC}"
apt-get update -y
apt-get install -y \
  python3-venv \
  python3-pip \
  python3-full \
  python3-lgpio \
  python3-picamera2 \
  libcamera-apps \
  i2c-tools \
  git \
  curl || true

# ── Set up directories ──
echo -e "\n${YELLOW}[2/7] Setting up installation directories in ${INSTALL_DIR}...${NC}"
mkdir -p "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR/model"
mkdir -p "$CONFIG_DIR"
mkdir -p "$DATA_DIR"

# Copy project files if not already in /opt/ai-trash-sorter
if [ "$REPO_ROOT" != "$INSTALL_DIR" ]; then
  echo "Syncing repository files to $INSTALL_DIR..."
  cp -r "$REPO_ROOT/raspberry-pi" "$INSTALL_DIR/"
  if [ -d "$REPO_ROOT/training/models" ]; then
    cp -r "$REPO_ROOT/training/models/"* "$INSTALL_DIR/model/" 2>/dev/null || true
  fi
  if [ -f "$INSTALL_DIR/model/waste-mobilenet-taco-kaggle-v1.tflite" ]; then
    cp "$INSTALL_DIR/model/waste-mobilenet-taco-kaggle-v1.tflite" "$INSTALL_DIR/model/model.tflite"
    cp "$INSTALL_DIR/model/waste-mobilenet-taco-kaggle-v1.json" "$INSTALL_DIR/model/model.json"
  fi
fi

chown -R "$REAL_USER:$REAL_USER" "$INSTALL_DIR" "$DATA_DIR"
chmod 755 "$DATA_DIR"

# ── Python venv ──
echo -e "\n${YELLOW}[3/7] Setting up Python virtual environment...${NC}"
VENV_DIR="$INSTALL_DIR/raspberry-pi/.venv"
if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv --system-site-packages "$VENV_DIR"
fi

"$VENV_DIR/bin/pip" install --upgrade pip
if [ -f "$INSTALL_DIR/raspberry-pi/requirements.txt" ]; then
  "$VENV_DIR/bin/pip" install -r "$INSTALL_DIR/raspberry-pi/requirements.txt" || true
fi

# ── Firebase config ──
echo -e "\n${YELLOW}[4/7] Configuring Firebase Realtime Database & Device Settings...${NC}"
DEFAULT_DB_URL="https://trash2444-default-rtdb.asia-southeast1.firebasedatabase.app"
DEFAULT_STORAGE="trash2444.firebasestorage.app"
DEFAULT_DEVICE="rpi-sorter-01"

read -r -p "Enter Firebase Realtime Database URL [$DEFAULT_DB_URL]: " INPUT_DB_URL
DB_URL="${INPUT_DB_URL:-$DEFAULT_DB_URL}"

read -r -p "Enter Firebase Storage Bucket [$DEFAULT_STORAGE]: " INPUT_STORAGE
STORAGE_BUCKET="${INPUT_STORAGE:-$DEFAULT_STORAGE}"

read -r -p "Enter Device ID [$DEFAULT_DEVICE]: " INPUT_DEVICE
DEVICE_ID="${INPUT_DEVICE:-$DEFAULT_DEVICE}"

read -r -p "Enter path to Firebase Service Account JSON (or press Enter to skip): " INPUT_CRED

CREDS_PATH=""
if [ -n "$INPUT_CRED" ] && [ -f "$INPUT_CRED" ]; then
  cp "$INPUT_CRED" "$CONFIG_DIR/firebase-service-account.json"
  chmod 600 "$CONFIG_DIR/firebase-service-account.json"
  chown "$REAL_USER:$REAL_USER" "$CONFIG_DIR/firebase-service-account.json"
  CREDS_PATH="$CONFIG_DIR/firebase-service-account.json"
elif [ -f "$CONFIG_DIR/firebase-service-account.json" ]; then
  CREDS_PATH="$CONFIG_DIR/firebase-service-account.json"
fi

cat > "$CONFIG_DIR/config.json" <<EOF
{
  "device_id": "$DEVICE_ID",
  "model_path": "$INSTALL_DIR/model/model.tflite",
  "model_metadata_path": "$INSTALL_DIR/model/model.json",
  "data_dir": "$DATA_DIR",
  "firebase_database_url": "$DB_URL",
  "firebase_storage_bucket": "$STORAGE_BUCKET",
  $( [ -n "$CREDS_PATH" ] && echo "\"firebase_credentials_path\": \"$CREDS_PATH\"," || echo "\"firebase_credentials_path\": null," )
  "display": "console",
  "steps_per_revolution": 600,
  "step_pulse_seconds": 0.003,
  "home_timeout_seconds": 20,
  "trigger_distance_cm": 7.0,
  "temporary_image_ttl_seconds": 86400
}
EOF
chmod 644 "$CONFIG_DIR/config.json"
chown "$REAL_USER:$REAL_USER" "$CONFIG_DIR/config.json"
echo -e "${GREEN}Configuration written to $CONFIG_DIR/config.json${NC}"

# ── Install systemd service ──
echo -e "\n${YELLOW}[5/7] Installing auto-start systemd service...${NC}"
SERVICE_FILE="/etc/systemd/system/ai-trash-sorter.service"
cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=Novi AI Trash Sorter Appliance Service
After=network.target local-fs.target

[Service]
Type=simple
User=$REAL_USER
Group=$REAL_USER
WorkingDirectory=$INSTALL_DIR/raspberry-pi
Environment=PYTHONPATH=$INSTALL_DIR/raspberry-pi/app
Environment=PYTHONUNBUFFERED=1
ExecStart=$INSTALL_DIR/raspberry-pi/.venv/bin/python -m main --config $CONFIG_DIR/config.json --confirm-actuators
Restart=always
RestartSec=3
KillMode=process
TimeoutStopSec=15

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable ai-trash-sorter.service
echo -e "${GREEN}Auto-start service enabled! (Will run automatically on every Pi boot)${NC}"

# ── Finalize ──
echo -e "\n${YELLOW}[6/7] Finalizing installation...${NC}"
chmod +x "$INSTALL_DIR/raspberry-pi/scripts/run_sorter.sh" 2>/dev/null || true
chmod +x "$INSTALL_DIR/raspberry-pi/start.sh" 2>/dev/null || true

# ── Verify ──
echo -e "\n${YELLOW}[7/7] Verifying installation...${NC}"
if [ -f "$INSTALL_DIR/model/model.tflite" ]; then
  echo -e "${GREEN}  Model file found.${NC}"
else
  echo -e "${RED}  WARNING: model.tflite not found in $INSTALL_DIR/model/${NC}"
  echo -e "${YELLOW}  Place your .tflite model there before starting the service.${NC}"
fi

if [ -f "$CONFIG_DIR/config.json" ]; then
  echo -e "${GREEN}  Config file found.${NC}"
else
  echo -e "${RED}  WARNING: config.json not found at $CONFIG_DIR/${NC}"
fi

echo -e "\n${GREEN}=====================================================${NC}"
echo -e "${GREEN}        Setup Completed Successfully!               ${NC}"
echo -e "${GREEN}=====================================================${NC}"
echo -e "To start the sorter service right now, run:"
echo -e "  ${BLUE}sudo systemctl start ai-trash-sorter${NC}"
echo -e "\nTo check live logs from the sorter:"
echo -e "  ${BLUE}sudo journalctl -u ai-trash-sorter -f${NC}"
echo -e "\nTo run a simulated test without motors:"
echo -e "  ${BLUE}cd $INSTALL_DIR/raspberry-pi && PYTHONPATH=app .venv/bin/python -m main --simulation --once${NC}"
echo -e "\nTo stop the sorter:"
echo -e "  ${BLUE}sudo systemctl stop ai-trash-sorter${NC}"
echo -e "====================================================="
