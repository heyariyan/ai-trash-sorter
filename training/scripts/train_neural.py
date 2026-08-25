"""Train and export the project's neural waste classifier.

This script runs on the development/training machine only. It uses transfer
learning with MobileNetV2, stratified train/validation/test splits, class
weights, augmentation, and full-integer TFLite conversion for Raspberry Pi
inference. Raw images and generated models stay outside Git.
"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CLASSES = ("BIODEGRADABLE", "PLASTIC", "METAL", "OTHER")


def load_manifest(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    with path.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            image = Path(row["path"])
            label = str(row["label"])
            if label not in CLASSES:
                raise ValueError(f"line {line_number}: unsupported label {label!r}")
            if not image.is_file():
                continue
            key = str(image.resolve())
            if key in seen:
                continue
            seen.add(key)
            rows.append({"path": str(image), "label": label})
    counts = Counter(row["label"] for row in rows)
    missing = [label for label in CLASSES if not counts[label]]
    if missing:
        raise ValueError(f"manifest has no readable samples for: {', '.join(missing)}")
    return rows


def stratified_split(
    rows: list[dict[str, str]],
    validation_ratio: float,
    test_ratio: float,
    seed: int,
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    """Split each class independently so every class appears in every split."""
    if validation_ratio <= 0 or test_ratio <= 0 or validation_ratio + test_ratio >= 1:
        raise ValueError("validation/test ratios must be positive and sum to less than one")
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["label"]].append(row)
    rng = random.Random(seed)
    train: list[dict[str, str]] = []
    validation: list[dict[str, str]] = []
    test: list[dict[str, str]] = []
    for label in CLASSES:
        class_rows = list(grouped[label])
        rng.shuffle(class_rows)
        if len(class_rows) < 3:
            raise ValueError(f"class {label} needs at least three readable images")
        test_count = max(1, round(len(class_rows) * test_ratio))
        validation_count = max(1, round(len(class_rows) * validation_ratio))
        if test_count + validation_count >= len(class_rows):
            validation_count = 1
            test_count = 1
        test.extend(class_rows[:test_count])
        validation.extend(class_rows[test_count : test_count + validation_count])
        train.extend(class_rows[test_count + validation_count :])
    rng.shuffle(train)
    rng.shuffle(validation)
    rng.shuffle(test)
    return train, validation, test


def class_weights(rows: list[dict[str, str]]) -> dict[int, float]:
    counts = Counter(row["label"] for row in rows)
    total = len(rows)
    return {index: total / (len(CLASSES) * counts[label]) for index, label in enumerate(CLASSES)}


def _tensorflow() -> Any:
    try:
        import tensorflow as tf

        return tf
    except ImportError as exc:
        raise SystemExit(
            "TensorFlow is required on the development machine. Install a supported "
            "tensorflow package, then rerun this training command."
        ) from exc


def _image_tensor(tf: Any, path: Any, image_size: int) -> Any:
    image = tf.io.read_file(path)
    image = tf.io.decode_image(image, channels=3, expand_animations=False)
    image.set_shape([None, None, 3])
    image = tf.image.resize(image, [image_size, image_size], antialias=True)
    return tf.cast(image, tf.float32) / 255.0


def _dataset(tf: Any, rows: list[dict[str, str]], image_size: int, batch_size: int, training: bool) -> Any:
    paths = [row["path"] for row in rows]
    labels = [CLASSES.index(row["label"]) for row in rows]
    dataset = tf.data.Dataset.from_tensor_slices((paths, labels))
    if training:
        dataset = dataset.shuffle(len(rows), seed=42, reshuffle_each_iteration=True)

    def load(path: Any, label: Any) -> tuple[Any, Any]:
        image = _image_tensor(tf, path, image_size)
        return image, label

    return dataset.map(load, num_parallel_calls=tf.data.AUTOTUNE).batch(batch_size).prefetch(tf.data.AUTOTUNE)


def _representative_dataset(tf: Any, rows: list[dict[str, str]], image_size: int, limit: int = 128):
    for row in rows[:limit]:
        image = _image_tensor(tf, tf.constant(row["path"]), image_size)
        yield [tf.expand_dims(image, axis=0)]


def train(args: argparse.Namespace) -> dict[str, Any]:
    tf = _tensorflow()
    tf.keras.utils.set_random_seed(args.seed)
    rows = load_manifest(args.manifest)
    train_rows, validation_rows, test_rows = stratified_split(
        rows, args.validation_ratio, args.test_ratio, args.seed
    )

    augmentation = tf.keras.Sequential(
        [
            tf.keras.layers.RandomFlip("horizontal"),
            tf.keras.layers.RandomRotation(0.08),
            tf.keras.layers.RandomZoom(0.15),
            tf.keras.layers.RandomContrast(0.15),
        ],
        name="waste_augmentation",
    )
    base = tf.keras.applications.MobileNetV2(
        input_shape=(args.image_size, args.image_size, 3),
        include_top=False,
        weights=None if args.weights == "none" else args.weights,
    )
    base.trainable = False
    inputs = tf.keras.Input(shape=(args.image_size, args.image_size, 3), name="image")
    x = augmentation(inputs)
    x = tf.keras.applications.mobilenet_v2.preprocess_input(x * 255.0)
    x = base(x, training=False)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    x = tf.keras.layers.Dropout(0.25)(x)
    outputs = tf.keras.layers.Dense(len(CLASSES), activation="softmax", name="class_probabilities")(x)
    model = tf.keras.Model(inputs, outputs, name="ai_trash_sorter_mobilenetv2")
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=args.learning_rate),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )

    train_ds = _dataset(tf, train_rows, args.image_size, args.batch_size, True)
    validation_ds = _dataset(tf, validation_rows, args.image_size, args.batch_size, False)
    test_ds = _dataset(tf, test_rows, args.image_size, args.batch_size, False)
    callbacks = [
        tf.keras.callbacks.EarlyStopping(monitor="val_accuracy", patience=5, restore_best_weights=True),
        tf.keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.25, patience=2, min_lr=1e-7),
    ]
    history = model.fit(
        train_ds,
        validation_data=validation_ds,
        epochs=args.epochs,
        class_weight=class_weights(train_rows),
        callbacks=callbacks,
        verbose=2,
    )

    if args.fine_tune_layers > 0:
        base.trainable = True
        for layer in base.layers[:-args.fine_tune_layers]:
            layer.trainable = False
        for layer in base.layers:
            if isinstance(layer, tf.keras.layers.BatchNormalization):
                layer.trainable = False
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=args.fine_tune_learning_rate),
            loss="sparse_categorical_crossentropy",
            metrics=["accuracy"],
        )
        model.fit(
            train_ds,
            validation_data=validation_ds,
            epochs=args.fine_tune_epochs,
            class_weight=class_weights(train_rows),
            callbacks=callbacks,
            verbose=2,
        )

    test_loss, test_accuracy = model.evaluate(test_ds, verbose=0)
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.representative_dataset = lambda: _representative_dataset(
        tf, train_rows, args.image_size
    )
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    converter.inference_input_type = tf.uint8
    converter.inference_output_type = tf.uint8
    tflite_bytes = converter.convert()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(tflite_bytes)

    metadata = {
        "format": "tflite_classifier_v1",
        "model_version": args.model_version,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "classes": list(CLASSES),
        "architecture": "MobileNetV2 transfer learning",
        "input": {"width": args.image_size, "height": args.image_size, "channels": 3},
        "quantization": "full integer weights and uint8 input/output",
        "deployment_status": "not_deployed",
        "dataset": {"manifest": str(args.manifest), "dataset_version": args.dataset_version},
        "metrics": {
            "test_accuracy": float(test_accuracy),
            "test_loss": float(test_loss),
            "train_samples": len(train_rows),
            "validation_samples": len(validation_rows),
            "test_samples": len(test_rows),
            "final_train_accuracy": float(history.history["accuracy"][-1]),
            "final_validation_accuracy": float(history.history["val_accuracy"][-1]),
        },
    }
    args.output.with_suffix(".json").write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="output .tflite path")
    parser.add_argument("--model-version", required=True)
    parser.add_argument("--dataset-version", required=True)
    parser.add_argument("--image-size", type=int, default=160)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--fine-tune-epochs", type=int, default=8)
    parser.add_argument("--fine-tune-layers", type=int, default=30)
    parser.add_argument("--weights", choices=("imagenet", "none"), default="imagenet")
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--fine-tune-learning-rate", type=float, default=1e-5)
    parser.add_argument("--validation-ratio", type=float, default=0.15)
    parser.add_argument("--test-ratio", type=float, default=0.15)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if args.image_size < 96 or args.batch_size <= 0 or args.epochs <= 0:
        raise SystemExit("image-size must be at least 96; batch-size and epochs must be positive")
    metadata = train(args)
    print(json.dumps({"model": str(args.output), "metrics": metadata["metrics"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
