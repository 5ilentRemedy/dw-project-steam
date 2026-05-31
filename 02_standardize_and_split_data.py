import ast
import json
import re

import numpy as np
import pandas as pd

from project_config import DATA_DIR, INITIAL_CSV, PREPARED_DIR, RAW_DIR, SELECTED_COLUMNS, UPDATE_CSV
from logging_config import setup_logging

logger = setup_logging("02_standardize_and_split_data")


JSON_RENAME = {
    "name": "Name",
    "release_date": "ReleaseDate",
    "price": "Price",
    "required_age": "RequiredAge",
    "windows": "Windows",
    "mac": "Mac",
    "linux": "Linux",
    "metacritic_score": "MetacriticScore",
    "user_score": "UserScore",
    "positive": "PositiveReviews",
    "negative": "NegativeReviews",
    "achievements": "Achievements",
    "peak_ccu": "PeakCCU",
    "average_playtime_forever": "PlaytimeForever",
    "developers": "Developers",
    "publishers": "Publishers",
    "categories": "Categories",
    "genres": "Genres",
    "tags": "Tags",
    "supported_languages": "Languages",
    "website": "Website",
    "support_url": "SupportUrl",
    "support_email": "SupportEmail",
    "estimated_owners": "EstimatedOwners",
}

CSV_RENAME = {
    "Release date": "ReleaseDate",
    "Required age": "RequiredAge",
    "Metacritic score": "MetacriticScore",
    "User score": "UserScore",
    "Peak CCU": "PeakCCU",
    "Average playtime forever": "PlaytimeForever",
    "Supported languages": "Languages",
    "Support url": "SupportUrl",
    "Support email": "SupportEmail",
    "Estimated owners": "EstimatedOwners",
    "Positive": "PositiveReviews",
    "Negative": "NegativeReviews",
}


def latest_source_file():
    logger.debug("Searching for latest source file...")
    files = sorted(list(RAW_DIR.glob("games_*.json")) + list(RAW_DIR.glob("games_*.csv")))
    if not files:
        files = sorted(list(DATA_DIR.glob("games_*.json")) + list(DATA_DIR.glob("games_*.csv")))
        files = [file for file in files if "staging" not in file.name]
    if not files:
        logger.error("No source file found. Run 01_download_from_kagglehub.py first.")
        raise FileNotFoundError("No source file found. Run 01_download_from_kagglehub.py first.")

    json_files = [file for file in files if file.suffix.lower() == ".json"]
    latest = json_files[-1] if json_files else files[-1]
    logger.info(f"Found latest source file: {latest}")
    return latest


def read_source(path):
    logger.info(f"Reading source data from: {path}")
    if path.suffix.lower() == ".json":
        logger.debug("Detected JSON format, parsing...")
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        df = pd.DataFrame.from_dict(data, orient="index")
        df.index.name = "AppID"
        df = df.reset_index().rename(columns=JSON_RENAME)
        logger.info(f"✓ Loaded {len(df):,} records from JSON")
        return df

    logger.debug("Detected CSV format, parsing...")
    df = pd.read_csv(path, low_memory=False).rename(columns=CSV_RENAME)
    logger.info(f"✓ Loaded {len(df):,} records from CSV")
    return df


def clean_list_or_text(value):
    if isinstance(value, list):
        return ", ".join(str(item).strip() for item in value if str(item).strip())
    if pd.isna(value):
        return ""

    text = str(value).strip()
    if text.startswith("[") and text.endswith("]"):
        try:
            parsed = ast.literal_eval(text)
            if isinstance(parsed, list):
                return ", ".join(str(item).strip() for item in parsed if str(item).strip())
        except (SyntaxError, ValueError):
            pass

    return re.sub(r"\s+", " ", text)


def standardize(df):
    logger.info(f"Starting data standardization on {len(df):,} records")
    logger.debug("Step 1: Ensuring all required columns exist...")
    
    for column in SELECTED_COLUMNS:
        if column not in df.columns and column not in {"HasWebsite", "HasSupport"}:
            df[column] = ""

    df = df[[column for column in SELECTED_COLUMNS if column not in {"HasWebsite", "HasSupport"}]].copy()
    logger.debug(f"✓ Selected {len(df.columns)} columns")

    text_columns = [
        "Name",
        "Developers",
        "Publishers",
        "Categories",
        "Genres",
        "Tags",
        "Languages",
        "Website",
        "SupportUrl",
        "SupportEmail",
        "EstimatedOwners",
    ]
    logger.debug("Step 2: Cleaning text columns...")
    for column in text_columns:
        df[column] = df[column].apply(clean_list_or_text)
    logger.debug(f"✓ Cleaned {len(text_columns)} text columns")

    numeric_columns = [
        "AppID",
        "Price",
        "RequiredAge",
        "MetacriticScore",
        "UserScore",
        "PositiveReviews",
        "NegativeReviews",
        "Achievements",
        "PeakCCU",
        "PlaytimeForever",
    ]
    logger.debug("Step 3: Converting numeric columns...")
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0)
    logger.debug(f"✓ Converted {len(numeric_columns)} numeric columns")

    logger.debug("Step 4: Standardizing platform columns...")
    for column in ["Windows", "Mac", "Linux"]:
        df[column] = (
            df[column]
            .astype(str)
            .str.strip()
            .str.lower()
            .map({"true": "True", "1": "True", "yes": "True"})
            .fillna("False")
        )
    logger.debug("✓ Platform columns standardized")

    logger.debug("Step 5: Parsing dates...")
    df["ReleaseDateParsed"] = pd.to_datetime(df["ReleaseDate"], errors="coerce")
    df["ReleaseDate"] = df["ReleaseDateParsed"].dt.strftime("%Y-%m-%d").fillna("")
    logger.debug("✓ Dates parsed")

    logger.debug("Step 6: Creating derived columns...")
    df["HasWebsite"] = df["Website"].str.len().gt(5).astype(int)
    df["HasSupport"] = (df["SupportUrl"].str.len().gt(5) | df["SupportEmail"].str.len().gt(5)).astype(int)
    logger.debug("✓ Derived columns created")
    
    logger.info("✓ Data standardization completed")
    return df.replace({np.nan: ""})


def split_70_30_by_release_date(df):
    logger.info(f"Splitting dataset: 70% initial / 30% update (by release date)")
    
    logger.debug("Separating records with/without release dates...")
    with_date = df[df["ReleaseDateParsed"].notna()].sort_values(["ReleaseDateParsed", "AppID"])
    without_date = df[df["ReleaseDateParsed"].isna()].sort_values("AppID")
    
    logger.debug(f"  - Records with date: {len(with_date):,}")
    logger.debug(f"  - Records without date: {len(without_date):,}")

    split_index = int(len(with_date) * 0.70)
    initial = pd.concat([with_date.iloc[:split_index], without_date], ignore_index=True)
    update = with_date.iloc[split_index:].copy()
    
    logger.info(f"✓ Split completed: initial={len(initial):,}, update={len(update):,}")

    return initial[SELECTED_COLUMNS], update[SELECTED_COLUMNS]


def main() -> None:
    logger.info("=" * 80)
    logger.info("DATA STANDARDIZATION AND SPLITTING")
    logger.info("=" * 80)
    
    source = latest_source_file()
    PREPARED_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {PREPARED_DIR}")

    logger.info("-" * 80)
    logger.info("READING SOURCE DATA")
    logger.info("-" * 80)
    df = read_source(source)
    
    logger.info("-" * 80)
    logger.info("STANDARDIZING DATA")
    logger.info("-" * 80)
    df = standardize(df)
    
    logger.info("-" * 80)
    logger.info("SPLITTING DATA")
    logger.info("-" * 80)
    initial, update = split_70_30_by_release_date(df)

    logger.info("-" * 80)
    logger.info("SAVING TO CSV FILES")
    logger.info("-" * 80)
    logger.info(f"Writing initial bulk file: {INITIAL_CSV}")
    initial.to_csv(INITIAL_CSV, index=False, encoding="utf-8-sig")
    logger.info(f"✓ Written {len(initial):,} rows to {INITIAL_CSV}")
    
    logger.info(f"Writing update file: {UPDATE_CSV}")
    update.to_csv(UPDATE_CSV, index=False, encoding="utf-8-sig")
    logger.info(f"✓ Written {len(update):,} rows to {UPDATE_CSV}")

    logger.info("=" * 80)
    logger.info("DATA PROCESSING COMPLETED SUCCESSFULLY")
    logger.info(f"Initial bulk file: {len(initial):,} rows")
    logger.info(f"Update file:       {len(update):,} rows")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()

