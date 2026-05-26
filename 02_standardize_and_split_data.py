import ast
import json
import re

import numpy as np
import pandas as pd

from project_config import DATA_DIR, INITIAL_CSV, PREPARED_DIR, RAW_DIR, SELECTED_COLUMNS, UPDATE_CSV


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
    files = sorted(list(RAW_DIR.glob("games_*.json")) + list(RAW_DIR.glob("games_*.csv")))
    if not files:
        files = sorted(list(DATA_DIR.glob("games_*.json")) + list(DATA_DIR.glob("games_*.csv")))
        files = [file for file in files if "staging" not in file.name]
    if not files:
        raise FileNotFoundError("No source file found. Run 01_download_from_kagglehub.py first.")

    json_files = [file for file in files if file.suffix.lower() == ".json"]
    return json_files[-1] if json_files else files[-1]


def read_source(path):
    if path.suffix.lower() == ".json":
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        df = pd.DataFrame.from_dict(data, orient="index")
        df.index.name = "AppID"
        return df.reset_index().rename(columns=JSON_RENAME)

    return pd.read_csv(path, low_memory=False).rename(columns=CSV_RENAME)


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
    for column in SELECTED_COLUMNS:
        if column not in df.columns and column not in {"HasWebsite", "HasSupport"}:
            df[column] = ""

    df = df[[column for column in SELECTED_COLUMNS if column not in {"HasWebsite", "HasSupport"}]].copy()

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
    for column in text_columns:
        df[column] = df[column].apply(clean_list_or_text)

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
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0)

    for column in ["Windows", "Mac", "Linux"]:
        df[column] = (
            df[column]
            .astype(str)
            .str.strip()
            .str.lower()
            .map({"true": "True", "1": "True", "yes": "True"})
            .fillna("False")
        )

    df["ReleaseDateParsed"] = pd.to_datetime(df["ReleaseDate"], errors="coerce")
    df["ReleaseDate"] = df["ReleaseDateParsed"].dt.strftime("%Y-%m-%d").fillna("")
    df["HasWebsite"] = df["Website"].str.len().gt(5).astype(int)
    df["HasSupport"] = (df["SupportUrl"].str.len().gt(5) | df["SupportEmail"].str.len().gt(5)).astype(int)
    return df.replace({np.nan: ""})


def split_70_30_by_release_date(df):
    with_date = df[df["ReleaseDateParsed"].notna()].sort_values(["ReleaseDateParsed", "AppID"])
    without_date = df[df["ReleaseDateParsed"].isna()].sort_values("AppID")

    split_index = int(len(with_date) * 0.70)
    initial = pd.concat([with_date.iloc[:split_index], without_date], ignore_index=True)
    update = with_date.iloc[split_index:].copy()

    return initial[SELECTED_COLUMNS], update[SELECTED_COLUMNS]


def main() -> None:
    source = latest_source_file()
    PREPARED_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Reading source: {source}")
    df = standardize(read_source(source))
    initial, update = split_70_30_by_release_date(df)

    initial.to_csv(INITIAL_CSV, index=False, encoding="utf-8-sig")
    update.to_csv(UPDATE_CSV, index=False, encoding="utf-8-sig")

    print(f"Initial bulk file: {INITIAL_CSV} ({len(initial):,} rows)")
    print(f"Update file:       {UPDATE_CSV} ({len(update):,} rows)")


if __name__ == "__main__":
    main()

