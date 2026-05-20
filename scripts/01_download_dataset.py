import shutil
from datetime import datetime
from pathlib import Path

import kagglehub

from config import KAGGLE_DATASET, RAW_DIR


def download_dataset() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print(f"Downloading Kaggle dataset: {KAGGLE_DATASET}")
    cache_path = kagglehub.dataset_download(KAGGLE_DATASET)
    print(f"Kaggle cache path: {cache_path}")

    copied = 0
    for source_path in sorted(Path(cache_path).rglob("*")):
        if source_path.is_file():
            destination = RAW_DIR / f"{source_path.stem}_{timestamp}{source_path.suffix}"
            shutil.copy2(source_path, destination)
            print(f"Copied {destination.name}")
            copied += 1

    print(f"Done. {copied} file(s) copied to {RAW_DIR}")


if __name__ == "__main__":
    download_dataset()
