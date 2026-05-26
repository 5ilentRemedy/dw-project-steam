import getpass
import re

import numpy as np
import pandas as pd
import pyodbc

from project_config import INITIAL_CSV, INITIAL_TABLE, SQL_DIR, SQL_PASSWORD, SQL_USER, needs_sql_password, sql_connection_string


def execute_sql_file(cursor, path):
    sql = path.read_text(encoding="utf-8")
    batches = re.split(r"^\s*GO\s*$", sql, flags=re.IGNORECASE | re.MULTILINE)
    for batch in batches:
        if batch.strip():
            cursor.execute(batch)


def load_csv(cursor, csv_path, table_name):
    df = pd.read_csv(csv_path, index_col=False).replace({np.nan: None})
    columns = list(df.columns)

    cursor.execute(f"TRUNCATE TABLE dbo.{table_name};")
    placeholders = ", ".join("?" for _ in columns)
    column_sql = ", ".join(f"[{column}]" for column in columns)
    insert_sql = f"INSERT INTO dbo.{table_name} ({column_sql}) VALUES ({placeholders});"

    cursor.fast_executemany = True
    cursor.executemany(insert_sql, [tuple(row) for row in df.to_numpy()])
    print(f"Loaded {len(df):,} rows into dbo.{table_name}.")


def main() -> None:
    if not INITIAL_CSV.exists():
        raise FileNotFoundError(f"Missing {INITIAL_CSV}. Run 02_standardize_and_split_data.py first.")

    password = SQL_PASSWORD or (getpass.getpass(f"Password for {SQL_USER}: ") if needs_sql_password() else None)
    with pyodbc.connect(sql_connection_string(password), autocommit=False) as conn:
        cursor = conn.cursor()
        execute_sql_file(cursor, SQL_DIR / "01_database_objects.sql")
        conn.commit()

        load_csv(cursor, INITIAL_CSV, INITIAL_TABLE)
        conn.commit()

        cursor.execute("EXEC dbo.usp_RebuildSteamWarehouse;")
        conn.commit()

    print("Initial bulk load and star schema rebuild completed.")


if __name__ == "__main__":
    main()
