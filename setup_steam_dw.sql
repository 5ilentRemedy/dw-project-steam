-- =======================================================================
-- SQL Server Script to Create Database, Load Staging, and Build Star Schema
-- =======================================================================

USE master;
GO

-- 1. Create the Database
IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'SteamDW')
BEGIN
    CREATE DATABASE SteamDW;
END
GO

USE SteamDW;
GO

-- 2. Create Staging Table
-- Using NVARCHAR for all staging columns to prevent BULK INSERT type conversion errors.
-- We will handle data type casting during the ETL insert phase.
DROP TABLE IF EXISTS stg_SteamGames;
CREATE TABLE stg_SteamGames (
    name NVARCHAR(1000),
    release_date NVARCHAR(255),
    price NVARCHAR(100),
    windows NVARCHAR(50),
    mac NVARCHAR(50),
    linux NVARCHAR(50),
    metacritic_score NVARCHAR(50),
    achievements NVARCHAR(50),
    categories NVARCHAR(MAX),
    genres NVARCHAR(MAX),
    user_score NVARCHAR(50),
    positive NVARCHAR(50),
    negative NVARCHAR(50)
);
GO

-- 3. Load Data into Staging Table
-- Update this path if the SQL Server is hosted on a different machine than where the CSV is located.
BULK INSERT stg_SteamGames
FROM 'c:\Users\matth\OneDrive\Atlantis\dw-project-steam\games_extracted.csv'
WITH (
    FORMAT = 'CSV',
    FIRSTROW = 2,           -- Skip header row
    FIELDQUOTE = '"',
    FIELDTERMINATOR = ',',
    ROWTERMINATOR = '\n',   
    CODEPAGE = '65001'      -- UTF-8 Encoding
);
GO

-- 4. Drop Existing Star Schema Tables (to allow re-running the script)
DROP TABLE IF EXISTS Bridge_GameCategory;
DROP TABLE IF EXISTS Bridge_GameGenre;
DROP TABLE IF EXISTS FactGameMetrics;
DROP TABLE IF EXISTS DimCategory;
DROP TABLE IF EXISTS DimGenre;
DROP TABLE IF EXISTS DimPlatform;
DROP TABLE IF EXISTS DimGame;
GO

-- 5. Create Star Schema Tables
CREATE TABLE DimGame (
    GameKey INT IDENTITY(1,1) PRIMARY KEY,
    Name NVARCHAR(1000),
    ReleaseDate NVARCHAR(255)
);

CREATE TABLE DimPlatform (
    PlatformKey INT IDENTITY(1,1) PRIMARY KEY,
    Windows BIT,
    Mac BIT,
    Linux BIT
);

CREATE TABLE DimGenre (
    GenreKey INT IDENTITY(1,1) PRIMARY KEY,
    GenreName NVARCHAR(255) UNIQUE
);

CREATE TABLE DimCategory (
    CategoryKey INT IDENTITY(1,1) PRIMARY KEY,
    CategoryName NVARCHAR(255) UNIQUE
);

CREATE TABLE FactGameMetrics (
    FactKey INT IDENTITY(1,1) PRIMARY KEY,
    GameKey INT FOREIGN KEY REFERENCES DimGame(GameKey),
    PlatformKey INT FOREIGN KEY REFERENCES DimPlatform(PlatformKey),
    Price DECIMAL(10,2),
    MetacriticScore INT,
    Achievements INT,
    UserScore INT,
    PositiveReviews INT,
    NegativeReviews INT
);

CREATE TABLE Bridge_GameGenre (
    GameKey INT FOREIGN KEY REFERENCES DimGame(GameKey),
    GenreKey INT FOREIGN KEY REFERENCES DimGenre(GenreKey),
    PRIMARY KEY (GameKey, GenreKey)
);

CREATE TABLE Bridge_GameCategory (
    GameKey INT FOREIGN KEY REFERENCES DimGame(GameKey),
    CategoryKey INT FOREIGN KEY REFERENCES DimCategory(CategoryKey),
    PRIMARY KEY (GameKey, CategoryKey)
);
GO

-- 6. ETL Phase: Populate Dimension Tables
PRINT 'Populating Dimensions...';

INSERT INTO DimGame (Name, ReleaseDate)
SELECT DISTINCT name, release_date
FROM stg_SteamGames
WHERE name IS NOT NULL AND name != '';

INSERT INTO DimPlatform (Windows, Mac, Linux)
SELECT DISTINCT 
    CASE WHEN windows = 'True' THEN 1 ELSE 0 END,
    CASE WHEN mac = 'True' THEN 1 ELSE 0 END,
    CASE WHEN linux = 'True' THEN 1 ELSE 0 END
FROM stg_SteamGames;

-- Populate Genres (Splitting comma-separated values)
INSERT INTO DimGenre (GenreName)
SELECT DISTINCT LTRIM(RTRIM(value))
FROM stg_SteamGames
CROSS APPLY STRING_SPLIT(genres, ',')
WHERE value IS NOT NULL AND LTRIM(RTRIM(value)) != '';

-- Populate Categories (Splitting comma-separated values)
INSERT INTO DimCategory (CategoryName)
SELECT DISTINCT LTRIM(RTRIM(value))
FROM stg_SteamGames
CROSS APPLY STRING_SPLIT(categories, ',')
WHERE value IS NOT NULL AND LTRIM(RTRIM(value)) != '';

GO

-- 7. ETL Phase: Populate Fact Table
PRINT 'Populating Fact Table...';

INSERT INTO FactGameMetrics (
    GameKey, PlatformKey, Price, MetacriticScore, 
    Achievements, UserScore, PositiveReviews, NegativeReviews
)
SELECT 
    dg.GameKey,
    dp.PlatformKey,
    TRY_CAST(stg.price AS DECIMAL(10,2)),
    TRY_CAST(stg.metacritic_score AS INT),
    TRY_CAST(stg.achievements AS INT),
    TRY_CAST(stg.user_score AS INT),
    TRY_CAST(stg.positive AS INT),
    TRY_CAST(stg.negative AS INT)
FROM stg_SteamGames stg
JOIN DimGame dg 
    ON stg.name = dg.Name 
    AND (stg.release_date = dg.ReleaseDate OR (stg.release_date IS NULL AND dg.ReleaseDate IS NULL))
JOIN DimPlatform dp 
    ON CASE WHEN stg.windows = 'True' THEN 1 ELSE 0 END = dp.Windows 
    AND CASE WHEN stg.mac = 'True' THEN 1 ELSE 0 END = dp.Mac 
    AND CASE WHEN stg.linux = 'True' THEN 1 ELSE 0 END = dp.Linux;
GO

-- 8. ETL Phase: Populate Bridge Tables
PRINT 'Populating Bridge Tables...';

INSERT INTO Bridge_GameGenre (GameKey, GenreKey)
SELECT DISTINCT dg.GameKey, dgen.GenreKey
FROM stg_SteamGames stg
JOIN DimGame dg 
    ON stg.name = dg.Name 
    AND (stg.release_date = dg.ReleaseDate OR (stg.release_date IS NULL AND dg.ReleaseDate IS NULL))
CROSS APPLY STRING_SPLIT(stg.genres, ',') s
JOIN DimGenre dgen ON dgen.GenreName = LTRIM(RTRIM(s.value));

INSERT INTO Bridge_GameCategory (GameKey, CategoryKey)
SELECT DISTINCT dg.GameKey, dc.CategoryKey
FROM stg_SteamGames stg
JOIN DimGame dg 
    ON stg.name = dg.Name 
    AND (stg.release_date = dg.ReleaseDate OR (stg.release_date IS NULL AND dg.ReleaseDate IS NULL))
CROSS APPLY STRING_SPLIT(stg.categories, ',') s
JOIN DimCategory dc ON dc.CategoryName = LTRIM(RTRIM(s.value));
GO

PRINT 'Data Warehouse Setup and ETL Complete!';
