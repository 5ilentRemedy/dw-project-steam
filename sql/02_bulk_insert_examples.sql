USE db_dw_project_steam;
GO

-- Optional manual SQL loading examples.
-- The Python scripts 03_load_initial_bulk_to_mssql.py and 04_load_update_to_mssql.py
-- already load CSV files with pyodbc. Use these only if SQL Server can access the file paths.

TRUNCATE TABLE dbo.stg_SteamGames;

BULK INSERT dbo.stg_SteamGames
FROM 'C:\Users\matth\OneDrive\Atlantis\dw-project-steam\output\steam_games_initial.csv'
WITH (
    FIRSTROW = 2,
    FIELDTERMINATOR = ',',
    ROWTERMINATOR = '0x0a',
    FORMAT = 'CSV',
    CODEPAGE = '65001',
    TABLOCK
);

EXEC dbo.usp_RebuildSteamWarehouse;
GO

TRUNCATE TABLE dbo.stg_SteamGames_Update;

BULK INSERT dbo.stg_SteamGames_Update
FROM 'C:\Users\matth\OneDrive\Atlantis\dw-project-steam\output\steam_games_update.csv'
WITH (
    FIRSTROW = 2,
    FIELDTERMINATOR = ',',
    ROWTERMINATOR = '0x0a',
    FORMAT = 'CSV',
    CODEPAGE = '65001',
    TABLOCK
);

EXEC dbo.usp_ApplySteamGamesUpdate;
GO
