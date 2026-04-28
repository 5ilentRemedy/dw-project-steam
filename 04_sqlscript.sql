USE db_dw_project_steam;
GO

PRINT '--- REKONSTRUKCJA: CZYSTA GWIAZDA BEZ MOSTKÓW ---';

-- 1. CZYSZCZENIE
DROP TABLE IF EXISTS Fact_GameMetrics;
DROP TABLE IF EXISTS Dim_Game;
DROP TABLE IF EXISTS Dim_Date;
DROP TABLE IF EXISTS Dim_Platform;
GO

-- 2. TWORZENIE TABEL WYMIARÓW
-- Wszystkie opisy (gatunki, deweloperzy) lądują bezpośrednio w Dim_Game jako tekst
CREATE TABLE Dim_Game (
    GameKey INT IDENTITY(1,1) PRIMARY KEY,
    AppID INT,
    Name NVARCHAR(1000),
    AllGenres NVARCHAR(MAX),
    AllCategories NVARCHAR(MAX),
    AllDevelopers NVARCHAR(MAX),
    AllPublishers NVARCHAR(MAX)
);

CREATE TABLE Dim_Date (
    DateKey INT PRIMARY KEY,
    FullDate DATE,
    Year INT,
    Month INT,
    Quarter INT
);

CREATE TABLE Dim_Platform (
    PlatformKey INT IDENTITY(1,1) PRIMARY KEY,
    PlatformName NVARCHAR(100)
);
GO

-- 3. TABELA FAKTÓW (Łączy się bezpośrednio z każdym wymiarem)
CREATE TABLE Fact_GameMetrics (
    FactKey INT IDENTITY(1,1) PRIMARY KEY,
    GameKey INT FOREIGN KEY REFERENCES Dim_Game(GameKey),
    DateKey INT FOREIGN KEY REFERENCES Dim_Date(DateKey),
    PlatformKey INT FOREIGN KEY REFERENCES Dim_Platform(PlatformKey),
    Price DECIMAL(10,2),
    MetacriticScore INT,
    PositiveReviews INT,
    NegativeReviews INT,
    TotalReviews INT
);
GO

-- 4. PROCES ETL (Wypełnianie)

-- Wypełnianie Dim_Game (Denormalizacja - zachowujemy listy przecinkowe)
INSERT INTO Dim_Game (AppID, Name, AllGenres, AllCategories, AllDevelopers, AllPublishers)
SELECT DISTINCT 
    TRY_CAST(AppID AS INT), 
    Name, 
    Genres, 
    Categories, 
    Developers, 
    Publishers
FROM stg_SteamGames
WHERE TRY_CAST(AppID AS INT) IS NOT NULL;

-- Wypełnianie Dim_Date
INSERT INTO Dim_Date (DateKey, FullDate, Year, Month, Quarter)
SELECT DISTINCT 
    CAST(FORMAT(TRY_CAST([Release date] AS DATE), 'yyyyMMdd') AS INT),
    TRY_CAST([Release date] AS DATE),
    YEAR(TRY_CAST([Release date] AS DATE)),
    MONTH(TRY_CAST([Release date] AS DATE)),
    DATEPART(qq, TRY_CAST([Release date] AS DATE))
FROM stg_SteamGames 
WHERE TRY_CAST([Release date] AS DATE) IS NOT NULL;

-- Rekord techniczny dla braku daty
IF NOT EXISTS (SELECT 1 FROM Dim_Date WHERE DateKey = -1)
    INSERT INTO Dim_Date (DateKey, FullDate, Year, Month, Quarter) VALUES (-1, NULL, NULL, NULL, NULL);

-- Wypełnianie Dim_Platform
INSERT INTO Dim_Platform (PlatformName)
SELECT DISTINCT 
    ISNULL(NULLIF(
        CASE WHEN TRY_CAST(Windows AS BIT)=1 THEN 'Win ' ELSE '' END + 
        CASE WHEN TRY_CAST(Mac AS BIT)=1 THEN 'Mac ' ELSE '' END + 
        CASE WHEN TRY_CAST(Linux AS BIT)=1 THEN 'Lin' ELSE '' END
    , ''), 'Brak danych')
FROM stg_SteamGames;

-- Wypełnianie Fact_GameMetrics
INSERT INTO Fact_GameMetrics (GameKey, DateKey, PlatformKey, Price, MetacriticScore, PositiveReviews, NegativeReviews, TotalReviews)
SELECT 
    dg.GameKey,
    ISNULL(CAST(FORMAT(TRY_CAST(stg.[Release date] AS DATE), 'yyyyMMdd') AS INT), -1),
    dp.PlatformKey,
    TRY_CAST(stg.Price AS DECIMAL(10,2)),
    TRY_CAST(stg.[Metacritic score] AS INT),
    TRY_CAST(stg.Positive AS INT),
    TRY_CAST(stg.Negative AS INT),
    TRY_CAST(stg.Positive AS INT) + TRY_CAST(stg.Negative AS INT)
FROM stg_SteamGames stg
JOIN Dim_Game dg ON dg.AppID = TRY_CAST(stg.AppID AS INT)
JOIN Dim_Platform dp ON dp.PlatformName = ISNULL(NULLIF(
        CASE WHEN TRY_CAST(stg.Windows AS BIT)=1 THEN 'Win ' ELSE '' END + 
        CASE WHEN TRY_CAST(stg.Mac AS BIT)=1 THEN 'Mac ' ELSE '' END + 
        CASE WHEN TRY_CAST(stg.Linux AS BIT)=1 THEN 'Lin' ELSE '' END
    , ''), 'Brak danych');

PRINT '--- SCHEMAT GWIAZDY ZBUDOWANY (3 WYMIARY -> 1 FAKT) ---';
GO