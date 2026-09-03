"""Fine-tune MobileNetV2 on Real-World + Augmented Waste Dataset and Export to TFLite."""

import json
import os
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

import numpy as np
import tensorflow as tf
from PIL import Image, ImageEnhance, ImageOps

CLASSES = ["BIODEGRADABLE", "PLASTIC", "METAL", "OTHER"]
IMG_SIZE = (160, 160)
BATCH_SIZE = 16
EPOCHS_WARMUP = 12
EPOCHS_FINETUNE = 15

DATASET_ROOT = Path(r"C:\Users\ariya\Desktop\Novi\training\dataset\real_world")
OUTPUT_DIR = Path(r"C:\Users\ariya\Desktop\Novi\training\models")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def generate_augmented_dataset(src_dir: Path, out_dir: Path, target_per_class: int = 250):
    """Generate heavily augmented training samples from real-world camera photos."""
    out_dir.mkdir(parents=True, exist_ok=True)
    for cat in CLASSES:
        (out_dir / cat).mkdir(parents=True, exist_ok=True)

    print(f"Augmenting images from {src_dir} to {out_dir} (target ~{target_per_class} per class)...")

    for cat in CLASSES:
        cat_src = src_dir / cat
        cat_out = out_dir / cat
        images = list(cat_src.glob("*.jpg")) + list(cat_src.glob("*.png"))
        
        # If class has few or no images (e.g. OTHER), generate variations from empty crops and mixed textures
        if not images and cat == "OTHER":
            # Generate empty background / miscellaneous synthetic tiles
            for i in range(target_per_class):
                # Random solid/gradient texture representing empty tray & miscellaneous
                gray_val = random.randint(30, 120)
                noise = np.random.randint(-15, 15, (160, 160, 3), dtype=np.int16)
                base = np.full((160, 160, 3), gray_val, dtype=np.int16) + noise
                base = np.clip(base, 0, 255).astype(np.uint8)
                img = Image.fromarray(base)
                img.save(str(cat_out / f"synth_other_{i:04d}.jpg"))
            print(f" - {cat}: generated {target_per_class} synthetic ambient/other samples.")
            continue

        print(f" - {cat}: {len(images)} source images -> generating {target_per_class} augmented samples...")
        
        count = 0
        while count < target_per_class:
            for src_path in images:
                if count >= target_per_class:
                    break
                try:
                    with Image.open(src_path) as img:
                        img = img.convert("RGB")
                        
                        # Apply random augmentations
                        if random.random() > 0.5:
                            img = img.transpose(Image.FLIP_LEFT_RIGHT)
                        if random.random() > 0.5:
                            img = img.transpose(Image.FLIP_TOP_BOTTOM)
                        
                        # Random rotation (-180 to 180)
                        angle = random.uniform(-180, 180)
                        img = img.rotate(angle, resample=Image.BILINEAR, expand=False)
                        
                        # Random crop / zoom
                        w, h = img.size
                        zoom = random.uniform(0.75, 1.0)
                        crop_w, crop_h = int(w * zoom), int(h * zoom)
                        left = random.randint(0, max(0, w - crop_w))
                        top = random.randint(0, max(0, h - crop_h))
                        img = img.crop((left, top, left + crop_w, top + crop_h))
                        
                        # Random brightness & contrast
                        enhancer = ImageEnhance.Brightness(img)
                        img = enhancer.enhance(random.uniform(0.7, 1.3))
                        enhancer = ImageEnhance.Contrast(img)
                        img = enhancer.enhance(random.uniform(0.8, 1.3))
                        
                        img = img.resize(IMG_SIZE, Image.BILINEAR)
                        img.save(str(cat_out / f"aug_{cat}_{count:04d}.jpg"), quality=85)
                        count += 1
                except Exception as e:
                    print(f"Error augmenting {src_path}: {e}")


def load_dataset(dataset_dir: Path):
    """Load image dataset with train/validation split."""
    ds_train = tf.keras.utils.image_dataset_from_directory(
        dataset_dir,
        labels="inferred",
        label_mode="categorical",
        class_names=CLASSES,
        color_mode="rgb",
        batch_size=BATCH_SIZE,
        image_size=IMG_SIZE,
        shuffle=True,
        seed=42,
        validation_split=0.2,
        subset="training",
    )

    ds_val = tf.keras.utils.image_dataset_from_directory(
        dataset_dir,
        labels="inferred",
        label_mode="categorical",
        class_names=CLASSES,
        color_mode="rgb",
        batch_size=BATCH_SIZE,
        image_size=IMG_SIZE,
        shuffle=False,
        seed=42,
        validation_split=0.2,
        subset="validation",
    )

    # Autotune prefetching
    AUTOTUNE = tf.data.AUTOTUNE
    ds_train = ds_train.prefetch(buffer_size=AUTOTUNE)
    ds_val = ds_val.prefetch(buffer_size=AUTOTUNE)

    return ds_train, ds_val


def build_model(num_classes=4):
    """Build MobileNetV2 with custom classification head."""
    # Preprocessing layer: scales [0, 255] to [-1, 1]
    preprocess_input = tf.keras.applications.mobilenet_v2.preprocess_input

    base_model = tf.keras.applications.MobileNetV2(
        input_shape=(160, 160, 3),
        include_top=False,
        weights="imagenet",
    )
    base_model.trainable = False

    inputs = tf.keras.Input(shape=(160, 160, 3))
    x = preprocess_input(inputs)
    x = base_model(x, training=False)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    x = tf.keras.layers.Dropout(0.3)(x)
    x = tf.keras.layers.Dense(128, activation="relu")(x)
    x = tf.keras.layers.Dropout(0.2)(x)
    outputs = tf.keras.layers.Dense(num_classes, activation="softmax", name="predictions")(x)

    model = tf.keras.Model(inputs, outputs, name="novi_mobilenet_v2")
    return model, base_model


def train_and_export():
    augmented_dir = Path(r"C:\Users\ariya\AppData\Local\Temp\novi_augmented_train")
    if augmented_dir.exists():
        shutil.rmtree(augmented_dir, ignore_errors=True)
    generate_augmented_dataset(DATASET_ROOT, augmented_dir, target_per_class=300)

    ds_train, ds_val = load_dataset(augmented_dir)

    print("\n" + "=" * 60)
    print("🚀 PHASE 1: Training Classification Head (Backbone Frozen)...")
    print("=" * 60)

    model, base_model = build_model(num_classes=len(CLASSES))
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    history1 = model.fit(
        ds_train,
        validation_data=ds_val,
        epochs=EPOCHS_WARMUP,
    )

    print("\n" + "=" * 60)
    print("🚀 PHASE 2: Fine-Tuning Top Layers of MobileNetV2...")
    print("=" * 60)

    base_model.trainable = True
    # Freeze bottom 100 layers, fine-tune top 54 layers
    for layer in base_model.layers[:100]:
        layer.trainable = False

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.0001),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    history2 = model.fit(
        ds_train,
        validation_data=ds_val,
        epochs=EPOCHS_FINETUNE,
    )

    # Evaluate final model
    val_loss, val_acc = model.evaluate(ds_val)
    print(f"\n✅ Final Validation Accuracy: {val_acc * 100:.2f}% (Loss: {val_loss:.4f})")

    # ── Export to Quantized TFLite ──
    print("\n📦 Converting to Optimized TensorFlow Lite model...")
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    
    tflite_model = converter.convert()

    tflite_path = OUTPUT_DIR / "waste-mobilenet-taco-kaggle-v1.tflite"
    json_path = OUTPUT_DIR / "waste-mobilenet-taco-kaggle-v1.json"

    tflite_path.write_bytes(tflite_model)
    print(f"✅ Exported TFLite Model: {tflite_path} ({len(tflite_model) / 1024 / 1024:.2f} MB)")

    metadata = {
        "architecture": "MobileNetV2 Real-World Fine-Tuned",
        "classes": CLASSES,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "format": "tflite_classifier_v1",
        "input": {"channels": 3, "height": 160, "width": 160},
        "metrics": {
            "validation_accuracy": float(val_acc),
            "validation_loss": float(val_loss),
            "classes": CLASSES,
        },
        "model_version": "waste-mobilenet-v2-realworld",
        "quantization": "dynamic range quantized int8 weights",
    }
    json_path.write_text(json.dumps(metadata, indent=2))
    print(f"✅ Exported Metadata: {json_path}")

    # Cleanup temp
    shutil.rmtree(augmented_dir, ignore_errors=True)
    print("\n🎉 Training & Export Complete!")


if __name__ == "__main__":
    train_and_export()
