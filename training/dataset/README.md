# Dataset bootstrap

## Source

The bootstrap sources are [Adithya Challa's Waste Classification dataset on Kaggle](https://www.kaggle.com/datasets/adithyachalla/waste-classification) and TACO (Trash Annotations in Context). Kaggle is downloaded on the development machine with `kagglehub`; TACO is supplied separately to the merger script.

Kaggle currently lists the dataset license as **Apache License 2.0**. This records the source terms observed during the M3 audit; review the Kaggle data card and any upstream terms again before redistribution or commercial use. The raw images are not committed to this repository.

The dataset contains nine source folders. They do not map one-to-one to this appliance's four classes, so the remapping is explicit and intentionally conservative:

| Source label | Project label | Reason |
| --- | --- | --- |
| Food Organics | BIODEGRADABLE | Organic food waste decomposes biologically |
| Vegetation | BIODEGRADABLE | Leaves and plant matter are biodegradable |
| Plastic | PLASTIC | Direct material match |
| Metal | METAL | Direct material match |
| Cardboard | BIODEGRADABLE | Paper/cardboard are biodegradable materials in this project |
| Glass | OTHER | Not one of the four current target classes |
| Paper | BIODEGRADABLE | Paper/cardboard are biodegradable materials in this project |
| Textile Trash | OTHER | Not one of the four current target classes |
| Miscellaneous Trash | OTHER | Unknown or mixed material |

TACO follows the same policy: all paper/cardboard/organic classes map to `BIODEGRADABLE`, all plastic classes map to `PLASTIC`, all metal classes map to `METAL`, and only unknown/unhandled classes map to `OTHER`. The merger is [training/dataset/merge_taco_kaggle.py](merge_taco_kaggle.py).

Important: TACO contains a much larger taxonomy than the merger's initial 16-name table. The full TACO category list and per-image source licenses must be audited before using a merged manifest for training or redistribution. The toolkit and dataset terms must be kept distinct; retain the original TACO attribution and image URLs from its annotations.

This is a bootstrap dataset, not domain-complete training data. Pi feedback images and owner-reviewed corrections take priority in later rounds.

## Reproduce the download and manifest

```text
uv run --with kagglehub --python 3.12 --no-project python training/dataset/download_kaggle.py
uv run --python 3.12 --no-project python training/dataset/remap_labels.py --root <downloaded-path> --output training/dataset/manifests/bootstrap.jsonl
```

The download script prints the cache path. Keep that path and all generated manifests local; only the scripts and this license/mapping record belong in Git.

For the merged plan, supply a local TACO checkout containing `annotations.json` and the image files:

```text
uv run --python 3.12 --no-project python training/dataset/merge_taco_kaggle.py --taco-root <taco-root> --kaggle-root <downloaded-path> --output training/dataset/manifests/taco-kaggle.jsonl
```
