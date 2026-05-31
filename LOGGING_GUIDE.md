# Logging System Documentation

## Overview

A comprehensive logging system has been added to all scripts in the Data Warehouse project. This system provides detailed tracking of:

- Specific steps executed by each script
- Processing progress and statistics
- Data transformations and database operations
- Connection status and authentication
- Errors and warnings with detailed context

## Logging Output

### Console Output
All scripts log to **both the console and log files** with formatted timestamps:

```
2026-05-31 10:45:23 | INFO     | Logging initialized for script: 02_standardize_and_split_data
2026-05-31 10:45:24 | INFO     | Reading source data from: data/raw/games_20260531_094925.json
2026-05-31 10:45:25 | INFO     | ✓ Loaded 50,000 records from JSON
```

### Log Files
Log files are automatically created in the `logs/` directory with timestamps:
- `00_setup_venv_20260531_104523.log`
- `01_download_from_kagglehub_20260531_104612.log`
- `02_standardize_and_split_data_20260531_104725.log`
- etc.

## Script-by-Script Logging Details

### 00_setup_venv.py
Logs the virtual environment creation process:
```
✓ Virtual environment created successfully
✓ Pip upgraded
✓ All packages installed successfully
```

### 00_test_mssql_connection.py
Tests database connections with detailed reporting:
```
SQL Server: localhost\SQLEXPRESS01
Target database: db_dw_project_steam
Authentication: SQL login (dashuser)
✓ Connected successfully to SERVER, database master
✓ Connected successfully to SERVER, database db_dw_project_steam
✓ ALL CONNECTION TESTS PASSED
```

### 01_download_from_kagglehub.py
Tracks download progress with file-by-file status:
```
Starting download from Kaggle dataset: fronkongames/steam-games-dataset
✓ Dataset downloaded to cache: C:\path\to\cache
Found 2 file(s) to process
  [  1/  2] ✓ games_20260531_094925.json (45.23 MB)
  [  2/  2] ✓ games_20260531_094926.csv (52.15 MB)
DOWNLOAD COMPLETED: 2/2 file(s) copied successfully
```

### 02_standardize_and_split_data.py
Detailed data processing steps:
```
READING SOURCE DATA
✓ Loaded 50,000 records from JSON

STANDARDIZING DATA
Step 1: Ensuring all required columns exist...
Step 2: Cleaning text columns...
Step 3: Converting numeric columns...
Step 4: Standardizing platform columns...
Step 5: Parsing dates...
Step 6: Creating derived columns...
✓ Data standardization completed

SPLITTING DATA
Separating records with/without release dates...
  - Records with date: 35,000
  - Records without date: 15,000
✓ Split completed: initial=28,000, update=22,000

SAVING TO CSV FILES
✓ Written 28,000 rows to output/steam_games_initial.csv
✓ Written 22,000 rows to output/steam_games_update.csv
```

### 03_load_initial_bulk_to_mssql.py
Tracks database operations:
```
CREATING DATABASE OBJECTS
Executing: 01_database_objects.sql
✓ Executed 5 SQL batch(es) from 01_database_objects.sql
✓ Database objects created

LOADING INITIAL DATA
Loading CSV data: output/steam_games_initial.csv
✓ Loaded 28,000 rows from CSV into memory
Truncating table dbo.stg_SteamGames...
Inserting 28,000 rows into dbo.stg_SteamGames...
✓ Loaded 28,000 rows into dbo.stg_SteamGames

REBUILDING STAR SCHEMA
Executing: dbo.usp_RebuildSteamWarehouse...
✓ Star schema rebuilt successfully
```

### 04_load_update_to_mssql.py
Similar tracking for update operations:
```
UPDATE DATA LOAD TO SQL SERVER
✓ Loaded 22,000 rows from CSV into memory
✓ Connected to SQL Server
Inserting 22,000 rows into dbo.stg_SteamGames_Update...
✓ Loaded 22,000 rows into dbo.stg_SteamGames_Update

APPLYING UPDATES TO STAR SCHEMA
Executing: dbo.usp_ApplySteamGamesUpdate...
✓ Star schema updated successfully
```

### 05_dashboard_streamlit.py
UI interaction logging:
```
DASHBOARD INITIALIZATION
Session state initialized
Loading data from SQL Server (cache timeout: 10 minutes)
✓ Data loaded successfully: 1,500,000 rows
Applying user filters...
Applied year filter: 2 year(s)
Applied platform filter: 1 platform(s)
Filters applied: 2 active filter(s) | Result: 125,000 rows
Data ready for display: 45,000 unique games
Rendering KPI metrics...
Rendering visualization charts...
✓ Dashboard rendered successfully
```

### 06_run_dashboard.py
Server launch logging:
```
STREAMLIT DASHBOARD LAUNCHER
Starting Streamlit server...
Dashboard URL: http://localhost:8501
Press Ctrl+C to stop the server
```

## Logging Features

### Progress Indicators
- ✓ Success indicators for completed operations
- ✗ Error indicators for failures
- Row counts, file sizes, and timing information
- Processing stages clearly marked

### Log Levels
- **DEBUG**: Detailed internal operations (stored in file)
- **INFO**: Normal operation flow (console + file)
- **ERROR**: Failures and exceptions (console + file)

### Structured Output
- Separator lines for major sections
- Hierarchical indentation for nested operations
- Consistent timestamp format (YYYY-MM-DD HH:MM:SS)
- Summary statistics after each phase

## Accessing Logs

### View Recent Logs
```powershell
# Get last 50 lines of latest log
Get-Content (Get-ChildItem logs/ -Latest 1).FullName -Tail 50

# Search logs for errors
Get-ChildItem logs/ | Select-String "ERROR" | Select -Last 20
```

### Monitor Real-Time
```powershell
# Follow log file as it's written
Get-Content (Get-ChildItem logs/ -Latest 1).FullName -Wait
```

## Example: Complete Data Pipeline Logs

When running the entire pipeline, you'll see comprehensive logs tracking:

1. **Setup Phase** → `00_setup_venv.py`
   - Virtual environment creation
   - Dependency installation

2. **Connection Test** → `00_test_mssql_connection.py`
   - Database connectivity validation
   - Authentication verification

3. **Data Download** → `01_download_from_kagglehub.py`
   - File download tracking
   - Copy progress with sizes

4. **Data Preparation** → `02_standardize_and_split_data.py`
   - Parsing, cleaning, and transformation steps
   - Data split statistics

5. **Database Load** → `03_load_initial_bulk_to_mssql.py` + `04_load_update_to_mssql.py`
   - Schema creation
   - Bulk data insertion
   - Star schema rebuild

6. **Dashboard** → `05_dashboard_streamlit.py` + `06_run_dashboard.py`
   - Data loading
   - Filter application
   - Rendering progress

All logs are saved to the `logs/` directory for future reference and debugging.
