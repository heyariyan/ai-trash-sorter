# Dataset bootstrap

## Source

The M3 bootstrap source is [Adithya Challa's Waste Classification dataset on Kaggle](https://www.kaggle.com/datasets/adithyachalla/waste-classification), downloaded on the development machine with `kagglehub` using the handle `adithyachalla/waste-classification`.

Kaggle currently lists the dataset license as **Apache License 2.0**. This records the source terms observed during the M3 audit; review the Kaggle data card and any upstream terms again before redistribution or commercial use. The raw images are not committed to this repository.

The dataset contains nine source folders. They do not map one-to-one to this appliance's four classes, so the remapping is explicit and intentionally conservative:

| Source label | Project label | Reason |
| --- | --- | --- |
| Food Organics | BIODEGRADABLE | Organic food waste decomposes biologically |
| Vegetation | BIODEGRADABLE | Leaves and plant matter are biodegradable |
| Plastic | PLASTIC | Direct material match |
| Metal | METAL | Direct material match |
| Cardboard | OTHER | Not one of the four current target classes |
| Glass | OTHER | Not one of the four current target classes |
| Paper | OTHER | Not one of the four current target classes |
| Textile Trash | OTHER | Not one of the four current target classes |
| Miscellaneous Trash | OTHER | Ambiguous mixed material |

This is a bootstrap dataset, not domain-complete training data. Pi feedback images and owner-reviewed corrections take priority in later rounds.

## Reproduce the download and manifest

```text
uv run --with kagglehub --python 3.12 --no-project python training/dataset/download_kaggle.py
uv run --python 3.12 --no-project python training/dataset/remap_labels.py --root <downloaded-path> --output training/dataset/manifests/bootstrap.jsonl
```

The download script prints the cache path. Keep that path and all generated manifests local; only the scripts and this license/mapping record belong in Git.
