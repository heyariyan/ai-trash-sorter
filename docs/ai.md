# M3 visual AI

Status: **Neural training/export pipeline implemented; a production model is not declared until training and Pi benchmarking complete.**

The first measured run is recorded in [model-evaluation.md](model-evaluation.md):
80.55% held-out accuracy and a Pi test deployment. One owner-confirmed plastic
sample was misclassified as `OTHER`, so deployment remains test-only.

## Material policy

The classifier has exactly four current outputs:

| Material policy | Project class |
| --- | --- |
| Organic waste, vegetation, paper, cardboard, cartons | `BIODEGRADABLE` |
| Plastic bottles, caps, containers, wrappers, film, utensils | `PLASTIC` |
| Metal cans, caps, foil, containers, aluminium, steel | `METAL` |
| Unknown, mixed, unsupported, glass, textile, rubber | `OTHER` |

This mapping is explicit in `training/dataset/remap_labels.py` and
`training/dataset/merge_taco_kaggle.py`. TACO images with multiple conflicting
material annotations are conservatively marked `OTHER` for image-level
classification; the source categories remain in the manifest for review.

## Dataset and training

1. Download Kaggle on the development machine with `download_kaggle.py`.
2. Supply a local TACO checkout to `merge_taco_kaggle.py`.
3. Review the generated JSONL manifest and source licenses before training.
4. Train with `training/scripts/train_neural.py`.

The training script uses a MobileNetV2 transfer-learning model, image
augmentation, stratified train/validation/test splits, class weighting, early
stopping, and optional fine-tuning. It exports a full-integer quantized TFLite
model plus a JSON sidecar. It does not use RGB centroids, color averages, or
any other non-neural classifier.

Example (development machine only):

```text
python training/scripts/train_neural.py \
  --manifest training/dataset/manifests/taco-kaggle.jsonl \
  --output training/models/waste-mobilenet-v1.tflite \
  --model-version waste-mobilenet-v1 \
  --dataset-version taco-plus-kaggle-reviewed-v1
```

`--weights imagenet` is the default for transfer learning. Use `--weights
none` only when the training machine must remain offline. The raw dataset,
manifest, checkpoints, and model binaries are ignored by Git.

## Pi runtime

`raspberry-pi/app/ai/inference.py` loads the TFLite model and its JSON sidecar,
preprocesses the image, handles float or quantized I/O, and returns:

`category`, `confidence`, `model_version`, `inference_time_ms`, `timestamp`.

The Pi needs a compatible `tflite-runtime` or `ai-edge-litert` wheel and NumPy;
the correct choice depends on the Pi OS architecture and Python version. The
model is loaded once and reused; network calls and model retraining are outside
the sorting loop. A model is not deployed until its sidecar records metrics,
input size, quantization, dataset version, and owner approval.

## Measurement gate

For every candidate model record test accuracy, per-class precision/recall,
confusion matrix, model size, cold-load time, and repeated Pi inference times.
Only measured values may be reported. Feedback from the Pi is human-reviewed
before it enters a later training round; there is no automatic retraining or
redeployment.
