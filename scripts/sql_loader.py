import getpass

import numpy as np
import pandas as pd
import pyodbc

from config import SQL_DATABASE, SQL_DRIVER, SQL_SERVER, SQL_USER


def connection_string(password):
    return (
        f"DRIVER={{{SQL_DRIVER}}};"
        f"SERVER={SQL_SERVER};"
        f"DATABASE={SQL_DATABASE};"
        f"UID={SQL_USER};"
        f"PWD={password};"
        "TrustServerCertificate=yes;"
    )


def load_csv_to_table(csv_path, table_name, password=None, replace_table=True):
    if not csv_path.exists():
        raise FileNotFoundError(f"Missing file: {csv_path}")

    password = password if password is not None else getpass.getpass(f"Password for {SQL_USER}: ")
    df = pd.read_csv(csv_path, index_col=False).replace({np.nan: None})

    print(f"Loading {csv_path.name} into dbo.{table_name}: {len(df):,} rows, {len(df.columns)} columns")
    conn = pyodbc.connect(connection_string(password))
    try:
        cursor = conn.cursor()
        cursor.fast_executemany = True

        if replace_table:
            cursor.execute(f"IF OBJECT_ID('dbo.{table_name}', 'U') IS NOT NULL DROP TABLE dbo.{table_name};")

        column_defs = ", ".join(f"[{column}] NVARCHAR(MAX)" for column in df.columns)
        cursor.execute(f"CREATE TABLE dbo.{table_name} ({column_defs});")
        conn.commit()

        columns = ", ".join(f"[{column}]" for column in df.columns)
        placeholders = ", ".join("?" for _ in df.columns)
        insert_sql = f"INSERT INTO dbo.{table_name} ({columns}) VALUES ({placeholders});"
        cursor.executemany(insert_sql, [tuple(row) for row in df.to_numpy()])
        conn.commit()
    finally:
        conn.close()

    print(f"Loaded dbo.{table_name}")


def execute_procedure(procedure_name, password=None):
    password = password if password is not None else getpass.getpass(f"Password for {SQL_USER}: ")
    conn = pyodbc.connect(connection_string(password), autocommit=True)
    try:
        cursor = conn.cursor()
        cursor.execute(f"EXEC dbo.{procedure_name};")
        while cursor.nextset():
            pass
    finally:
        conn.close()

    print(f"Executed dbo.{procedure_name}")

