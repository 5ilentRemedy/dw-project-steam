# Steam Data Warehouse

Main project stream: Kaggle data ingestion, MS SQL Server data warehouse, and a Java Spring Boot dashboard.

The pipeline downloads the Steam games dataset from Kaggle, splits it by release date into an initial 70% data source and a later 30% update source, loads the initial source to MS SQL Server, builds the star schema in SQL, and serves analytics through Spring Boot.

## Project Layout

- `scripts/01_download_dataset.py` downloads the Kaggle dataset with `kagglehub` into `data/raw/`.
- `scripts/02_prepare_data_sources.py` creates `data/prepared/steam_games_initial.csv` and `data/prepared/steam_games_update.csv`.
- `scripts/03_load_initial_to_sql.py` loads the 70% initial data source into `dbo.stg_SteamGames`.
- `sql/01_star_schema.sql` creates the stored procedures and star schema objects.
- `scripts/04_load_update_to_sql.py` loads the 30% update source into `dbo.stg_SteamGames_Update`, merges it into staging, and rebuilds the warehouse.
- `dashboard-springboot/` contains the Java Spring Boot dashboard.

## Configuration

Python scripts read these optional environment variables:

- `KAGGLE_DATASET`, default `fronkongames/steam-games-dataset`
- `STEAM_SQL_SERVER`, default `NORMANDY\SQLEXPRESS01`
- `STEAM_SQL_DATABASE`, default `db_dw_project_steam`
- `STEAM_SQL_USER`, default `dashuser`
- `STEAM_SQL_DRIVER`, default `ODBC Driver 17 for SQL Server`

The Spring Boot app reads:

- `STEAM_JDBC_URL`, default `jdbc:sqlserver://localhost;instanceName=SQLEXPRESS01;databaseName=db_dw_project_steam;encrypt=true;trustServerCertificate=true`
- `STEAM_SQL_USER`, default `dashuser`
- `STEAM_SQL_PASSWORD`, default empty

Set `STEAM_JDBC_URL` or edit `dashboard-springboot/src/main/resources/application.properties` if your SQL Server host or instance is different.

## Run Order

```powershell
pip install -r requirements.txt
python scripts/01_download_dataset.py
python scripts/02_prepare_data_sources.py
python scripts/03_load_initial_to_sql.py
```

Then run `sql/01_star_schema.sql` in SQL Server Management Studio or Azure Data Studio, and execute:

```sql
EXEC dbo.usp_RebuildSteamWarehouse;
```

For the later 30% data update:

```powershell
python scripts/04_load_update_to_sql.py
```

To start the dashboard:

```powershell
cd dashboard-springboot
$env:STEAM_SQL_PASSWORD = "your_password"
mvn spring-boot:run
```

Open `http://localhost:8080`.
