# M3 visual AI baseline

Status: **M3 v0 complete: baseline trained, local inference verified, and temporary Pi inference passed.**

## Dataset

The development machine downloaded Kaggle dataset version 1 for `adithyachalla/waste-classification` with `kagglehub`. Kaggle lists the dataset as Apache 2.0 and describes nine source folders. The explicit remapping is recorded in [training/dataset/README.md](../training/dataset/README.md).

The downloaded manifest contains 4,752 images:

| Project class | Images |
| --- | ---: |
| BIODEGRADABLE | 847 |
| METAL | 790 |
| OTHER | 2,194 |
| PLASTIC | 921 |

Raw images and generated manifests remain outside Git.

## Baseline model

The M3 baseline is a deliberately transparent RGB-centroid classifier. It resizes images to 8x8 RGB pixels, computes one centroid per class, and selects the nearest centroid. It is not the final quantized neural model and must not be presented as production accuracy.

| Field | Value |
| --- | --- |
| Model version | `baseline-rgb-centroid-v0` |
| Training samples | 800 |
| Holdout samples | 200 |
| Holdout accuracy | 0.515 |
| Input | 8x8 RGB |
| Quantization | None; float JSON baseline |
| Deployment status | Temporary Pi verification only; not production-deployed |

One local sample from the dataset's Plastic folder was classified as `OTHER` with a 34.11% score. This is expected evidence that the baseline needs a real visual model and domain-specific Pi feedback before it can control a sorter.

## Runtime path

`raspberry-pi/app/ai/inference.py` loads the same JSON format and returns `category`, `confidence`, `model_version`, `inference_time_ms`, and `timestamp`. It performs no GPIO, motor, servo, network, or database work.

The baseline was copied temporarily to `/tmp` on the Pi and run against `/home/ariyan/Pictures/ai-trash-sorter-20260824-155418.jpg`. It returned `OTHER` with a 0.318736 score and measured `inference_time_ms=316.986`. The temporary model, module, and runner were removed after the test; no permanent model or code was installed.

## Next work

1. Replace the RGB-centroid baseline with a small image model suitable for TFLite/quantized deployment.
2. Evaluate on owner-reviewed Pi images before any deployment approval.
3. Begin M4 object detection using U1, without coupling it to motor movement.
