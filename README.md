# Steam Data Warehouse

Projekt jest oparty na Pythonie, MS SQL Server i dashboardzie Streamlit.

## Co robi pipeline

1. Pobiera dane ze zbioru Kaggle przez `kagglehub`.
2. Standaryzuje dane i zostawia tylko kolumny potrzebne do hurtowni.
3. Dzieli dane według daty premiery gry w proporcji 70/30:
   - 70% starszych rekordów jako initial bulk load,
   - 30% nowszych rekordów jako osobny update.
4. Ładuje initial dataset do tabeli stagingowej w MS SQL Server.
5. Tworzy schemat gwiazdy: wymiary oraz jedną tabelę faktów.
6. Pozwala później dociągnąć update i przebudować schemat gwiazdy.
7. Uruchamia dashboard Streamlit z KPI i 6 wykresami.

Pliki CSV po podziale trafiają do katalogu `output/`.

## Pliki projektu

```text
project_config.py
01_download_from_kagglehub.py
02_standardize_and_split_data.py
03_load_initial_bulk_to_mssql.py
04_load_update_to_mssql.py
05_dashboard_streamlit.py
06_run_dashboard.py
requirements.txt
```

```text
sql/01_database_objects.sql
sql/02_bulk_insert_examples.sql
```

## Konfiguracja

Domyślne ustawienia są w `project_config.py`.

Możesz je nadpisać zmiennymi środowiskowymi:

```powershell
$env:STEAM_SQL_SERVER = "NORMANDY\SQLEXPRESS01"
$env:STEAM_SQL_DATABASE = "db_dw_project_steam"
$env:STEAM_SQL_USER = "dashuser"
$env:STEAM_SQL_PASSWORD = "your_password"
```

Domyślna lokalna instancja to `localhost\SQLEXPRESS`. Jeśli używasz Windows Authentication zamiast loginu SQL:

```powershell
$env:STEAM_SQL_TRUSTED_CONNECTION = "1"
```

## Uruchomienie

Opcjonalnie utwórz lokalne środowisko `.venv` i zainstaluj zależności:

```powershell
python 00_setup_venv.py
.\.venv\Scripts\Activate.ps1
```

Albo zainstaluj zależności bezpośrednio w aktywnym Pythonie:

```powershell
pip install -r requirements.txt
```

Pipeline:

```powershell
python 01_download_from_kagglehub.py
python 02_standardize_and_split_data.py
python 00_test_mssql_connection.py
python 03_load_initial_bulk_to_mssql.py
python 04_load_update_to_mssql.py
python 06_run_dashboard.py
```

Dashboard można też uruchomić bezpośrednio:

```powershell
streamlit run 05_dashboard_streamlit.py
```

## SQL

`sql/01_database_objects.sql` zawiera:

- tabele stagingowe,
- procedurę czyszczenia schematu gwiazdy,
- procedurę budowania wymiarów i tabeli faktów,
- procedurę przebudowy hurtowni,
- procedurę aplikowania update.

`sql/02_bulk_insert_examples.sql` to opcjonalny przykład ręcznego ładowania CSV przez SQL Server. Główny pipeline ładuje dane przez Python/pyodbc.
