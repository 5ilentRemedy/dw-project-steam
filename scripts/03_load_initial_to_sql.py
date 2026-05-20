from config import INITIAL_STAGING_TABLE, PREPARED_DIR
from sql_loader import execute_procedure, load_csv_to_table


def main() -> None:
    load_csv_to_table(PREPARED_DIR / "steam_games_initial.csv", INITIAL_STAGING_TABLE)
    print("Run sql/01_star_schema.sql in SQL Server once if procedures are not installed yet.")
    print("Then execute: EXEC dbo.usp_CleanStarSchema; EXEC dbo.usp_BuildAndLoadStarSchema;")


if __name__ == "__main__":
    main()

