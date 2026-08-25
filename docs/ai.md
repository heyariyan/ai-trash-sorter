# M3 visual AI baseline

Status: **M3 v0 verified; remapping policy changed and the baseline must be retrained before use.**

## Dataset

The development machine downloaded Kaggle dataset version 1 for `adithyachalla/waste-classification` with `kagglehub`. Kaggle lists the dataset as Apache 2.0 and describes nine source folders. The explicit remapping is recorded in [training/dataset/README.md](../training/dataset/README.md).

The previous Kaggle-only manifest contained 4,752 images. That manifest and its model used an older mapping in which paper/cardboard were `OTHER`; those metrics are retained for history but are invalid for the new policy.

The new merged training plan is:

| Source material | Project class |
| --- | ---: |
| Organic, vegetation, paper, cardboard | BIODEGRADABLE |
| Plastic items, bottles, caps, containers | PLASTIC |
| Metal items, cans, caps, containers | METAL |
| Unknown, mixed, or unsupported material | OTHER |

Raw images and generated manifests remain outside Git.

## Baseline model

The M3 baseline is a deliberately transparent RGB-centroid classifier. It resizes images to 8x8 RGB pixels, computes one centroid per class, and selects the nearest centroid. It is not the final quantized neural model and must not be presented as production accuracy. It must be retrained after the TACO+Kaggle merge and corrected material mapping.

| Field | Value |
| --- | --- |
| Model version | `baseline-rgb-centroid-v0` |
| Training samples | 800 |
| Holdout samples | 200 |
| Holdout accuracy | 0.515 |
| Input | 8x8 RGB |
| Quantization | None; float JSON baseline |
| Deployment status | Temporary Pi verification only; not production-deployed |

The old baseline's local sample and Pi checks remain historical evidence only. New evaluation must use the corrected merged manifest and owner-reviewed material labels.

## Runtime path

`raspberry-pi/app/ai/inference.py` loads the same JSON format and returns `category`, `confidence`, `model_version`, `inference_time_ms`, and `timestamp`. It performs no GPIO, motor, servo, network, or database work.

The baseline was copied temporarily to `/tmp` on the Pi and run against `/home/ariyan/Pictures/ai-trash-sorter-20260824-155418.jpg`. It returned `OTHER` with a 0.318736 score and measured `inference_time_ms=316.986`. The temporary model, module, and runner were removed after the test; no permanent model or code was installed.

## Next work

1. Audit and extend the TACO category mapping beyond the initial 16-name table.
2. Merge TACO and Kaggle with the corrected four-class policy, then retrain and evaluate.
3. Replace the RGB-centroid baseline with a small image model suitable for TFLite/quantized deployment.
4. Evaluate on owner-reviewed Pi images before any deployment approval.
5. Continue M4 object detection using U1, without coupling it to motor movement.
