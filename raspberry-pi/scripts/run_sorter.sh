#!/bin/bash
set -euo pipefail
export PYTHONPATH=/opt/ai-trash-sorter/raspberry-pi/app
export PYTHONUNBUFFERED=1
exec /opt/ai-trash-sorter/raspberry-pi/.venv/bin/python -m main \
    --config /etc/ai-trash-sorter/config.json --confirm-actuators "$@"
