import ast
import json
import re

import numpy as np
import pandas as pd

from config import PREPARED_DIR, RAW_DIR, SELECTED_COLUMNS


JSON_RENAME = {
    "name": "Name",
    "release_date": "Release date",
    "price": "Price",
    "required_age": "Required age",
    "windows": "Windows",
    "mac": "Mac",
    "linux": "Linux",
    "metacritic_score": "Metacritic score",
    "user_score": "User score",
    "positive": "Positive",
    "negative": "Negative",
    "achievements": "Achievements",
    "peak_ccu": "Peak CCU",
    "average_playtime_forever": "Playtime forever",
    "developers": "Developers",
    "publishers": "Publishers",
    "categories": "Categories",
    "genres": "Genres",
    "tags": "Tags",
    "supported_languages": "Languages",
    "website": "Website",
    "support_url": "Support URL",
    "support_email": "Support Email",
    "estimated_owners": "Estimated owners",
}

CSV_RENAME = {
    "Supported languages": "Languages",
    "Support url": "Support URL",
    "Support email": "Support Email",
    "Average playtime forever": "Playtime forever",
}


def latest_source_file():
    files = sorted(list(RAW_DIR.glob("games_*.json")) + list(RAW_DIR.glob("games_*.csv")))
    if not files:
        legacy_files = sorted(list((RAW_DIR.parent).glob("games_*.json")) + list((RAW_DIR.parent).glob("games_*.csv")))
        legacy_files = [file for file in legacy_files if "staging" not in file.name]
        files = legacy_files
    if not files:
        raise FileNotFoundError("No Kaggle source file found. Run scripts/01_download_dataset.py first.")
    json_files = [file for file in files if file.suffix.lower() == ".json"]
    return json_files[-1] if json_files else files[-1]


def read_source(path):
    if path.suffix.lower() == ".json":
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        df = pd.DataFrame.from_dict(data, orient="index")
        df.index.name = "AppID"
        df = df.reset_index()
        return df.rename(columns=JSON_RENAME)

    return pd.read_csv(path, low_memory=False).rename(columns=CSV_RENAME)


def clean_list_value(value):
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


def prepare_dataframe(df):
    for column in SELECTED_COLUMNS:
        if column not in df.columns and column not in {"Has Website", "Has Support"}:
            df[column] = ""

    df = df[[column for column in SELECTED_COLUMNS if column not in {"Has Website", "Has Support"}]].copy()

    text_columns = [
        "Name",
        "Developers",
        "Publishers",
        "Categories",
        "Genres",
        "Tags",
        "Languages",
        "Website",
        "Support URL",
        "Support Email",
        "Estimated owners",
    ]
    for column in text_columns:
        df[column] = df[column].apply(clean_list_value)

    numeric_columns = [
        "AppID",
        "Price",
        "Required age",
        "Metacritic score",
        "User score",
        "Positive",
        "Negative",
        "Achievements",
        "Peak CCU",
        "Playtime forever",
    ]
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0)

    for column in ["Windows", "Mac", "Linux"]:
        df[column] = df[column].astype(str).str.strip().str.lower().map({"true": "True", "1": "True"}).fillna("False")

    df["Release date parsed"] = pd.to_datetime(df["Release date"], errors="coerce")
    df["Release date"] = df["Release date parsed"].dt.strftime("%Y-%m-%d").fillna("")
    df["Has Website"] = df["Website"].str.len().gt(5).astype(int)
    df["Has Support"] = (df["Support URL"].str.len().gt(5) | df["Support Email"].str.len().gt(5)).astype(int)

    df = df.replace({np.nan: ""})
    return df


def split_by_release_date(df):
    valid = df[df["Release date parsed"].notna()].sort_values(["Release date parsed", "AppID"]).copy()
    missing = df[df["Release date parsed"].isna()].sort_values("AppID").copy()

    split_index = int(len(valid) * 0.70)
    initial = pd.concat([valid.iloc[:split_index], missing], ignore_index=True)
    update = valid.iloc[split_index:].copy()

    return initial[SELECTED_COLUMNS], update[SELECTED_COLUMNS]


def prepare_data_sources() -> None:
    source = latest_source_file()
    PREPARED_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Reading source: {source}")
    df = prepare_dataframe(read_source(source))
    initial, update = split_by_release_date(df)

    initial_path = PREPARED_DIR / "steam_games_initial.csv"
    update_path = PREPARED_DIR / "steam_games_update.csv"

    initial.to_csv(initial_path, index=False, encoding="utf-8-sig")
    update.to_csv(update_path, index=False, encoding="utf-8-sig")

    print(f"Initial source: {initial_path} ({len(initial):,} rows)")
    print(f"Update source:  {update_path} ({len(update):,} rows)")


if __name__ == "__main__":
    prepare_data_sources()

