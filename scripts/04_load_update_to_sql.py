import getpass

from config import SQL_USER, UPDATE_STAGING_TABLE, PREPARED_DIR
from sql_loader import execute_procedure, load_csv_to_table


def main() -> None:
    password = getpass.getpass(f"Password for {SQL_USER}: ")
    load_csv_to_table(PREPARED_DIR / "steam_games_update.csv", UPDATE_STAGING_TABLE, password=password)
    execute_procedure("usp_ApplySteamGamesUpdate", password=password)


if __name__ == "__main__":
    main()

