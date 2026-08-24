"""Download the M3 bootstrap dataset on the development machine only."""

from __future__ import annotations

from pathlib import Path


DATASET_HANDLE = "adithyachalla/waste-classification"


def main() -> int:
    try:
        import kagglehub
    except ImportError as exc:
        raise SystemExit(
            "kagglehub is required on the development machine; use uv run --with kagglehub"
        ) from exc

    path = Path(kagglehub.dataset_download(DATASET_HANDLE))
    print(f"dataset_path={path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
