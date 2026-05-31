import getpass

import pyodbc

from project_config import (
    SQL_DATABASE,
    SQL_PASSWORD,
    SQL_SERVER,
    SQL_TRUSTED_CONNECTION,
    SQL_USER,
    needs_sql_password,
    sql_connection_string,
)
from logging_config import setup_logging

logger = setup_logging("00_test_mssql_connection")


def test_database(database, password):
    logger.info(f"Testing connection to database: {database}")
    try:
        with pyodbc.connect(sql_connection_string(password, database=database)) as conn:
            cursor = conn.cursor()
            logger.debug(f"Connected successfully, executing test query...")
            cursor.execute("SELECT @@SERVERNAME AS ServerName, DB_NAME() AS DatabaseName;")
            row = cursor.fetchone()
            logger.info(f"✓ Connected successfully to {row.ServerName}, database {row.DatabaseName}")
            return True
    except Exception as e:
        logger.error(f"✗ Connection failed: {e}")
        return False


def main() -> None:
    logger.info("=" * 80)
    logger.info("SQL SERVER CONNECTION TEST")
    logger.info("=" * 80)
    logger.info(f"SQL Server: {SQL_SERVER}")
    logger.info(f"Target database: {SQL_DATABASE}")
    auth_type = "Windows trusted connection" if SQL_TRUSTED_CONNECTION else f"SQL login ({SQL_USER})"
    logger.info(f"Authentication: {auth_type}")

    password = None
    if needs_sql_password():
        logger.info("SQL password required")
        password = SQL_PASSWORD or getpass.getpass(f"Password for {SQL_USER}: ")
    else:
        logger.info("Using Windows trusted connection (no password required)")

    logger.info("-" * 80)
    logger.info("Testing SQL Server instance via master database...")
    logger.info("-" * 80)
    master_ok = test_database("master", password)

    logger.info("-" * 80)
    logger.info("Testing project database...")
    logger.info("-" * 80)
    project_ok = test_database(SQL_DATABASE, password)

    logger.info("=" * 80)
    if master_ok and project_ok:
        logger.info("✓ ALL CONNECTION TESTS PASSED")
    else:
        logger.error("✗ SOME CONNECTION TESTS FAILED")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()

