from datetime import datetime
from pathlib import Path
import shutil

import kagglehub

from project_config import KAGGLE_DATASET, RAW_DIR


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print(f"Downloading Kaggle dataset: {KAGGLE_DATASET}")
    cache_path = Path(kagglehub.dataset_download(KAGGLE_DATASET))
    print(f"Dataset cache: {cache_path}")

    copied = 0
    for source in sorted(cache_path.rglob("*")):
        if not source.is_file():
            continue
        destination = RAW_DIR / f"{source.stem}_{timestamp}{source.suffix}"
        shutil.copy2(source, destination)
        print(f"Copied: {destination}")
        copied += 1

    print(f"Done. Copied {copied} file(s) to {RAW_DIR}.")


if __name__ == "__main__":
    main()

