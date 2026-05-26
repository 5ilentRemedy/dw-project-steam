import getpass

import numpy as np
import pandas as pd
import pyodbc

from project_config import SQL_PASSWORD, SQL_USER, UPDATE_CSV, UPDATE_TABLE, needs_sql_password, sql_connection_string


def main() -> None:
    if not UPDATE_CSV.exists():
        raise FileNotFoundError(f"Missing {UPDATE_CSV}. Run 02_standardize_and_split_data.py first.")

    password = SQL_PASSWORD or (getpass.getpass(f"Password for {SQL_USER}: ") if needs_sql_password() else None)
    df = pd.read_csv(UPDATE_CSV, index_col=False).replace({np.nan: None})

    with pyodbc.connect(sql_connection_string(password), autocommit=False) as conn:
        cursor = conn.cursor()
        cursor.fast_executemany = True

        cursor.execute(f"TRUNCATE TABLE dbo.{UPDATE_TABLE};")
        columns = list(df.columns)
        column_sql = ", ".join(f"[{column}]" for column in columns)
        placeholders = ", ".join("?" for _ in columns)
        cursor.executemany(
            f"INSERT INTO dbo.{UPDATE_TABLE} ({column_sql}) VALUES ({placeholders});",
            [tuple(row) for row in df.to_numpy()],
        )
        conn.commit()

        cursor.execute("EXEC dbo.usp_ApplySteamGamesUpdate;")
        conn.commit()

    print(f"Loaded {len(df):,} update rows and rebuilt the star schema.")


if __name__ == "__main__":
    main()
