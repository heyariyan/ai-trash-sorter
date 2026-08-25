# Neural model evaluation

Evaluation date: 2026-08-25 (Asia/Kolkata)

## Training run

The development machine merged the cached Kaggle version 1 source with a
bounded TACO subset downloaded from the official annotations. The TACO subset
contained 79 successfully downloaded images after source URL failures were
skipped (20 `BIODEGRADABLE`, 20 `METAL`, 20 `OTHER`, 19 `PLASTIC`). The merged
manifest contained 4,831 readable images.

| Field | Measured value |
| --- | --- |
| Model version | `waste-mobilenet-taco-kaggle-v1` |
| Architecture | MobileNetV2 transfer learning + fine-tuning |
| Input | 160 × 160 RGB |
| Quantization | Full integer TFLite; uint8 input/output |
| Train / validation / test | 3,381 / 725 / 725 |
| Test accuracy | 0.805517 (80.55%) |
| Test loss | 0.499122 |
| TFLite size | approximately 2.62 MiB |
| Deployment status | Test-only copy on the Pi; not production-approved |

The dataset license and per-image source terms still govern redistribution;
raw images and model binaries remain outside Git.

## Raspberry Pi test

The Pi is a 64-bit ARM Raspberry Pi 3B+ running Python 3.13.5. An isolated
virtual environment was created at
`/home/ariyan/.venvs/ai-trash-sorter` with `ai-edge-litert` 2.2.0. The model,
sidecar, and inference runtime were copied to
`/home/ariyan/ai-trash-sorter-test/`; no actuator was started.

| Image | Prediction | Confidence | Inference time |
| --- | --- | ---: | ---: |
| Coca-Cola can WEBP (owner-confirmed metal) | `METAL` | 98.44% | 705.947 ms |
| Owner-confirmed plastic JPG | `OTHER` | 60.55% | 285.638 ms |
| Pi capture `ai-trash-sorter-20260824-155046.jpg` | `BIODEGRADABLE` | 93.36% | 315.368 ms |
| Pi capture `ai-trash-sorter-20260824-155418.jpg` | `BIODEGRADABLE` | 73.83% | 313.740 ms |

The can result is correct. The confirmed plastic result is incorrect, so this
model is functional but not yet production-accurate. The plastic image must be
added to the owner-reviewed feedback set before the next training round.
