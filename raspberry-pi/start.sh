#!/bin/bash
set -euo pipefail
ROOT=/opt/ai-trash-sorter/raspberry-pi
export PYTHONPATH="$ROOT/app"
export PYTHONUNBUFFERED=1
exec "$ROOT/.venv/bin/python" -m main --config /etc/ai-trash-sorter/config.json --confirm-actuators "$@"
