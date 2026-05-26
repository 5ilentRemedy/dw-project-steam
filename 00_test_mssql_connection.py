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


def test_database(database, password):
    with pyodbc.connect(sql_connection_string(password, database=database)) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT @@SERVERNAME AS ServerName, DB_NAME() AS DatabaseName;")
        row = cursor.fetchone()
        print(f"OK: connected to {row.ServerName}, database {row.DatabaseName}")


def main() -> None:
    print(f"SQL server: {SQL_SERVER}")
    print(f"Target database: {SQL_DATABASE}")
    print(f"Authentication: {'Windows trusted connection' if SQL_TRUSTED_CONNECTION else f'SQL login ({SQL_USER})'}")

    password = None
    if needs_sql_password():
        password = SQL_PASSWORD or getpass.getpass(f"Password for {SQL_USER}: ")

    print("\nTesting SQL Server instance via master database...")
    test_database("master", password)

    print("\nTesting project database...")
    test_database(SQL_DATABASE, password)


if __name__ == "__main__":
    main()

