#!/usr/bin/env bash
set -e
export PYTHONPATH=/home/ariyan/ai-trash-sorter-test/app
export PYTHONUNBUFFERED=1
exec /home/ariyan/.venvs/ai-trash-sorter/bin/python -m runner.local_runner \
    --model /home/ariyan/ai-trash-sorter-test/model/waste-mobilenet-taco-kaggle-v1.tflite \
    --confirm-movement \
    --display ssd1306 \
    --steps-per-revolution 600 \
    --stepper-pulse-delay-ms 3 \
    --gate-settle-seconds 0.2 \
    --presence-threshold-cm 7 \
    --buffer-dir /var/lib/ai-trash-sorter/runtime \
    --capture-dir /var/lib/ai-trash-sorter/images "$@"
