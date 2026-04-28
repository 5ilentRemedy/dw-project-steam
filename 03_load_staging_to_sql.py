import pandas as pd
import pyodbc
from pathlib import Path
import time
import sys
import io
import numpy as np
import getpass  # <--- Biblioteka do bezpiecznego pobierania hasła z CLI

# Wymuszenie kodowania UTF-8 dla konsoli Windows
if sys.stdout.encoding and 'utf' not in sys.stdout.encoding.lower():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def load_to_sql():
    print("=" * 60)
    print("ŁADOWANIE DANYCH STAGINGOWYCH DO MS SQL (CZYSTE PYODBC)")
    print("=" * 60)

    # --- KONFIGURACJA BAZY DANYCH ---
    db_user = 'dashuser'
    db_server = 'NORMANDY\\SQLEXPRESS' # <-- Zmień, jeśli instancja nazywa się inaczej
    db_name = 'db_dw_project_steam'
    table_name = 'stg_SteamGames'

    # Bezpieczne pobranie hasła od użytkownika (znaki nie będą widoczne na ekranie)
    db_password = getpass.getpass(prompt=f'Podaj hasło dla użytkownika {db_user}: ')

    data_dir = Path(__file__).parent / "data"
    input_file = data_dir / "games_staging.csv"

    if not input_file.exists():
        print(f"[!] BŁĄD: Nie znaleziono pliku {input_file.name}.")
        print("Uruchom najpierw skrypt 02_prepare_staging.py!")
        return

    print(f"\nWczytywanie {input_file.name} do pamięci...")
    # Zabezpieczenie przed przesunięciem kolumn
    df = pd.read_csv(input_file, index_col=False)
    
    # PyODBC nie radzi sobie z pandasowym NaN, zamieniamy je na czyste None (NULL w SQL)
    df = df.replace({np.nan: None})
    
    print(f"Dane wczytane: {df.shape[0]} wierszy, {df.shape[1]} kolumn.")

    # Tworzenie połączenia pyodbc z logowaniem SQL Server (użytkownik + hasło)
    conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={db_server};DATABASE={db_name};UID={db_user};PWD={db_password}"
    
    try:
        print("\nŁączenie z bazą danych...")
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # Włączamy fast_executemany dla drastycznego przyspieszenia BULK INSERTU
        cursor.fast_executemany = True

        print(f"Przygotowywanie tabeli '{table_name}' (usuwanie starej, jeśli istnieje)...")
        # Zrzucenie starej tabeli
        cursor.execute(f"IF OBJECT_ID('{table_name}', 'U') IS NOT NULL DROP TABLE {table_name};")
        
        # Tworzymy wszystkie kolumny jako NVARCHAR(MAX). 
        columns_def = ", ".join([f"[{col}] NVARCHAR(MAX)" for col in df.columns])
        create_table_sql = f"CREATE TABLE {table_name} ({columns_def});"
        cursor.execute(create_table_sql)
        conn.commit()

        print("Wgrywanie danych...")
        start_time = time.time()

        # Budowanie zapytania INSERT INTO
        placeholders = ", ".join(["?"] * len(df.columns))
        insert_sql = f"INSERT INTO {table_name} VALUES ({placeholders})"

        # Konwersja DataFrame na listę krotek
        records = [tuple(row) for row in df.to_numpy()]

        # Paczkowanie danych i wysyłanie na serwer
        cursor.executemany(insert_sql, records)
        conn.commit()
        
        elapsed_time = time.time() - start_time
        print(f"\n[SUKCES] Załadowano {df.shape[0]} rekordów do tabeli '{table_name}'.")
        print(f"Czas operacji: {elapsed_time:.2f} sekund.")

    except pyodbc.InterfaceError as e:
        print("\n[!] BŁĄD LOGOWANIA: Odmowa dostępu. Upewnij się, że wpisałeś poprawne hasło.")
        print(str(e))
    except Exception as e:
        print("\n[!] Wystąpił błąd bazy danych:")
        print(str(e))
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    load_to_sql()