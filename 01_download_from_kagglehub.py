from datetime import datetime
from pathlib import Path
import shutil

import kagglehub

from project_config import KAGGLE_DATASET, RAW_DIR
from logging_config import setup_logging

logger = setup_logging("01_download_from_kagglehub")


def main() -> None:
    logger.info("=" * 80)
    logger.info("KAGGLE DATASET DOWNLOAD")
    logger.info("=" * 80)
    
    logger.info(f"Creating raw data directory: {RAW_DIR}")
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("✓ Directory ready")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger.info(f"Timestamp for output files: {timestamp}")

    logger.info("-" * 80)
    logger.info(f"Starting download from Kaggle dataset: {KAGGLE_DATASET}")
    logger.info("-" * 80)
    
    try:
        cache_path = Path(kagglehub.dataset_download(KAGGLE_DATASET))
        logger.info(f"✓ Dataset downloaded to cache: {cache_path}")
    except Exception as e:
        logger.error(f"✗ Failed to download dataset: {e}")
        raise

    logger.info("-" * 80)
    logger.info(f"Copying files to {RAW_DIR}")
    logger.info("-" * 80)
    
    copied = 0
    file_list = sorted([f for f in cache_path.rglob("*") if f.is_file()])
    total_files = len(file_list)
    
    logger.info(f"Found {total_files} file(s) to process")
    
    for idx, source in enumerate(file_list, 1):
        destination = RAW_DIR / f"{source.stem}_{timestamp}{source.suffix}"
        try:
            shutil.copy2(source, destination)
            file_size_mb = source.stat().st_size / (1024 * 1024)
            logger.info(f"  [{idx:3d}/{total_files}] ✓ {destination.name} ({file_size_mb:.2f} MB)")
            copied += 1
        except Exception as e:
            logger.error(f"  [{idx:3d}/{total_files}] ✗ Failed to copy {source.name}: {e}")

    logger.info("=" * 80)
    logger.info(f"DOWNLOAD COMPLETED: {copied}/{total_files} file(s) copied successfully")
    logger.info(f"Output directory: {RAW_DIR}")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()

