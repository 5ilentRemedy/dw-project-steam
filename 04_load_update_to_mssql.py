import getpass

import numpy as np
import pandas as pd
import pyodbc

from project_config import SQL_PASSWORD, SQL_USER, UPDATE_CSV, UPDATE_TABLE, needs_sql_password, sql_connection_string
from logging_config import setup_logging

logger = setup_logging("04_load_update_to_mssql")


def main() -> None:
    logger.info("=" * 80)
    logger.info("UPDATE DATA LOAD TO SQL SERVER")
    logger.info("=" * 80)
    
    if not UPDATE_CSV.exists():
        logger.error(f"Missing file: {UPDATE_CSV}")
        logger.error("Run 02_standardize_and_split_data.py first.")
        raise FileNotFoundError(f"Missing {UPDATE_CSV}. Run 02_standardize_and_split_data.py first.")

    logger.info(f"Update CSV file found: {UPDATE_CSV}")

    logger.info("-" * 80)
    logger.info("LOADING UPDATE DATA")
    logger.info("-" * 80)
    
    logger.debug(f"Reading CSV file into memory...")
    df = pd.read_csv(UPDATE_CSV, index_col=False).replace({np.nan: None})
    logger.info(f"✓ Loaded {len(df):,} rows from CSV into memory")

    logger.info("-" * 80)
    logger.info("CONNECTING TO SQL SERVER")
    logger.info("-" * 80)
    
    password = SQL_PASSWORD or (getpass.getpass(f"Password for {SQL_USER}: ") if needs_sql_password() else None)
    
    try:
        with pyodbc.connect(sql_connection_string(password), autocommit=False) as conn:
            cursor = conn.cursor()
            logger.info("✓ Connected to SQL Server")
            
            cursor.fast_executemany = True

            logger.info(f"Truncating table dbo.{UPDATE_TABLE}...")
            cursor.execute(f"TRUNCATE TABLE dbo.{UPDATE_TABLE};")
            logger.debug("✓ Table truncated")
            
            columns = list(df.columns)
            logger.debug(f"Columns to load ({len(columns)}): {', '.join(columns[:5])}..." if len(columns) > 5 else f"Columns: {', '.join(columns)}")
            
            column_sql = ", ".join(f"[{column}]" for column in columns)
            placeholders = ", ".join("?" for _ in columns)
            
            logger.info(f"Inserting {len(df):,} rows into dbo.{UPDATE_TABLE}...")
            cursor.executemany(
                f"INSERT INTO dbo.{UPDATE_TABLE} ({column_sql}) VALUES ({placeholders});",
                [tuple(row) for row in df.to_numpy()],
            )
            conn.commit()
            logger.info(f"✓ Loaded {len(df):,} rows into dbo.{UPDATE_TABLE}")

            logger.info("-" * 80)
            logger.info("APPLYING UPDATES TO STAR SCHEMA")
            logger.info("-" * 80)
            logger.info("Executing: dbo.usp_ApplySteamGamesUpdate...")
            cursor.execute("EXEC dbo.usp_ApplySteamGamesUpdate;")
            conn.commit()
            logger.info("✓ Star schema updated successfully")
            
            logger.info("=" * 80)
            logger.info("✓ UPDATE LOAD AND STAR SCHEMA UPDATE COMPLETED SUCCESSFULLY")
            logger.info(f"Processed {len(df):,} update rows")
            logger.info("=" * 80)
    except Exception as e:
        logger.error(f"✗ Error during update load: {e}")
        raise


if __name__ == "__main__":
    main()
