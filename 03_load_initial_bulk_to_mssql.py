import getpass
import re

import numpy as np
import pandas as pd
import pyodbc

from project_config import INITIAL_CSV, INITIAL_TABLE, SQL_DIR, SQL_PASSWORD, SQL_USER, needs_sql_password, sql_connection_string
from logging_config import setup_logging

logger = setup_logging("03_load_initial_bulk_to_mssql")


def execute_sql_file(cursor, path):
    logger.info(f"Executing SQL file: {path}")
    sql = path.read_text(encoding="utf-8")
    batches = re.split(r"^\s*GO\s*$", sql, flags=re.IGNORECASE | re.MULTILINE)
    
    batch_count = len([b for b in batches if b.strip()])
    logger.debug(f"Found {batch_count} SQL batch(es)")
    
    executed = 0
    for idx, batch in enumerate(batches, 1):
        if batch.strip():
            logger.debug(f"  Executing batch {idx}...")
            cursor.execute(batch)
            executed += 1
    
    logger.info(f"✓ Executed {executed} SQL batch(es) from {path.name}")


def load_csv(cursor, csv_path, table_name):
    logger.info(f"Loading CSV data: {csv_path}")
    logger.debug(f"  Target table: dbo.{table_name}")
    
    df = pd.read_csv(csv_path, index_col=False).replace({np.nan: None})
    logger.info(f"✓ Loaded {len(df):,} rows from CSV into memory")
    
    columns = list(df.columns)
    logger.debug(f"Columns to load ({len(columns)}): {', '.join(columns[:5])}..." if len(columns) > 5 else f"Columns: {', '.join(columns)}")

    logger.info(f"Truncating table dbo.{table_name}...")
    cursor.execute(f"TRUNCATE TABLE dbo.{table_name};")
    logger.debug("✓ Table truncated")
    
    placeholders = ", ".join("?" for _ in columns)
    column_sql = ", ".join(f"[{column}]" for column in columns)
    insert_sql = f"INSERT INTO dbo.{table_name} ({column_sql}) VALUES ({placeholders});"

    logger.info(f"Inserting {len(df):,} rows into dbo.{table_name}...")
    cursor.fast_executemany = True
    cursor.executemany(insert_sql, [tuple(row) for row in df.to_numpy()])
    logger.info(f"✓ Loaded {len(df):,} rows into dbo.{table_name}")


def main() -> None:
    logger.info("=" * 80)
    logger.info("INITIAL BULK LOAD TO SQL SERVER")
    logger.info("=" * 80)
    
    if not INITIAL_CSV.exists():
        logger.error(f"Missing file: {INITIAL_CSV}")
        logger.error("Run 02_standardize_and_split_data.py first.")
        raise FileNotFoundError(f"Missing {INITIAL_CSV}. Run 02_standardize_and_split_data.py first.")

    logger.info(f"CSV file found: {INITIAL_CSV}")

    logger.info("-" * 80)
    logger.info("CONNECTING TO SQL SERVER")
    logger.info("-" * 80)
    
    password = SQL_PASSWORD or (getpass.getpass(f"Password for {SQL_USER}: ") if needs_sql_password() else None)
    
    try:
        with pyodbc.connect(sql_connection_string(password), autocommit=False) as conn:
            cursor = conn.cursor()
            logger.info("✓ Connected to SQL Server")
            
            logger.info("-" * 80)
            logger.info("CREATING DATABASE OBJECTS")
            logger.info("-" * 80)
            execute_sql_file(cursor, SQL_DIR / "01_database_objects.sql")
            conn.commit()
            logger.info("✓ Database objects created")

            logger.info("-" * 80)
            logger.info("LOADING INITIAL DATA")
            logger.info("-" * 80)
            load_csv(cursor, INITIAL_CSV, INITIAL_TABLE)
            conn.commit()
            logger.info("✓ Data committed to database")

            logger.info("-" * 80)
            logger.info("REBUILDING STAR SCHEMA")
            logger.info("-" * 80)
            logger.info("Executing: dbo.usp_RebuildSteamWarehouse...")
            cursor.execute("EXEC dbo.usp_RebuildSteamWarehouse;")
            conn.commit()
            logger.info("✓ Star schema rebuilt successfully")

            logger.info("=" * 80)
            logger.info("✓ INITIAL BULK LOAD AND STAR SCHEMA REBUILD COMPLETED SUCCESSFULLY")
            logger.info("=" * 80)
    except Exception as e:
        logger.error(f"✗ Error during bulk load: {e}")
        raise


if __name__ == "__main__":
    main()
