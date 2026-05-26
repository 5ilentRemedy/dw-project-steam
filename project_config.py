from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PREPARED_DIR = PROJECT_ROOT / "output"
SQL_DIR = PROJECT_ROOT / "sql"

KAGGLE_DATASET = os.getenv("KAGGLE_DATASET", "fronkongames/steam-games-dataset")

SQL_SERVER = os.getenv("STEAM_SQL_SERVER", r"localhost\SQLEXPRESS")
SQL_DATABASE = os.getenv("STEAM_SQL_DATABASE", "db_dw_project_steam")
SQL_USER = os.getenv("STEAM_SQL_USER", "dashuser")
SQL_PASSWORD = os.getenv("STEAM_SQL_PASSWORD")
SQL_DRIVER = os.getenv("STEAM_SQL_DRIVER", "ODBC Driver 17 for SQL Server")
SQL_TRUSTED_CONNECTION = os.getenv("STEAM_SQL_TRUSTED_CONNECTION", "0").lower() in {"1", "true", "yes"}

INITIAL_CSV = PREPARED_DIR / "steam_games_initial.csv"
UPDATE_CSV = PREPARED_DIR / "steam_games_update.csv"

INITIAL_TABLE = "stg_SteamGames"
UPDATE_TABLE = "stg_SteamGames_Update"

SELECTED_COLUMNS = [
    "AppID",
    "Name",
    "ReleaseDate",
    "Price",
    "RequiredAge",
    "Windows",
    "Mac",
    "Linux",
    "MetacriticScore",
    "UserScore",
    "PositiveReviews",
    "NegativeReviews",
    "Achievements",
    "PeakCCU",
    "PlaytimeForever",
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
    "HasWebsite",
    "HasSupport",
]


def needs_sql_password() -> bool:
    return not SQL_TRUSTED_CONNECTION


def sql_connection_string(password: str | None = None, database: str | None = None) -> str:
    auth = "Trusted_Connection=yes;" if SQL_TRUSTED_CONNECTION else f"UID={SQL_USER};PWD={password};"
    return (
        f"DRIVER={{{SQL_DRIVER}}};"
        f"SERVER={SQL_SERVER};"
        f"DATABASE={database or SQL_DATABASE};"
        f"{auth}"
        "TrustServerCertificate=yes;"
        "Connection Timeout=5;"
    )
