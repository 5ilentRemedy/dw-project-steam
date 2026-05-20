from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PREPARED_DIR = DATA_DIR / "prepared"

KAGGLE_DATASET = os.getenv("KAGGLE_DATASET", "fronkongames/steam-games-dataset")

SQL_SERVER = os.getenv("STEAM_SQL_SERVER", r"NORMANDY\SQLEXPRESS01")
SQL_DATABASE = os.getenv("STEAM_SQL_DATABASE", "db_dw_project_steam")
SQL_USER = os.getenv("STEAM_SQL_USER", "dashuser")
SQL_DRIVER = os.getenv("STEAM_SQL_DRIVER", "ODBC Driver 17 for SQL Server")

INITIAL_STAGING_TABLE = "stg_SteamGames"
UPDATE_STAGING_TABLE = "stg_SteamGames_Update"

SELECTED_COLUMNS = [
    "AppID",
    "Name",
    "Release date",
    "Price",
    "Required age",
    "Windows",
    "Mac",
    "Linux",
    "Metacritic score",
    "User score",
    "Positive",
    "Negative",
    "Achievements",
    "Peak CCU",
    "Playtime forever",
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
    "Has Website",
    "Has Support",
]

