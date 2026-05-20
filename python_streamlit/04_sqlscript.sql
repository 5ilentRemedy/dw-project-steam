USE db_dw_project_steam;
GO

-- ==============================================================================
-- 1. TWORZENIE PROCEDURY CZYSZCZĄCEJ
-- ==============================================================================
CREATE OR ALTER PROCEDURE dbo.usp_CleanStarSchema
AS
BEGIN
    PRINT '--- CZYSZCZENIE SCHEMATU ---';
    -- Kolejność usuwania ze względu na klucze obce
    DROP TABLE IF EXISTS dbo.Fact_GameMetrics;
    DROP TABLE IF EXISTS dbo.Dim_Game;
    DROP TABLE IF EXISTS dbo.Dim_Date;
    DROP TABLE IF EXISTS dbo.Dim_Platform;
    DROP TABLE IF EXISTS dbo.Dim_AgeRating;
    DROP TABLE IF EXISTS dbo.Dim_Language;
    DROP TABLE IF EXISTS dbo.Dim_SupportLevel;
    DROP TABLE IF EXISTS dbo.Dim_ContentStats;
    DROP TABLE IF EXISTS dbo.Dim_Genres;
    DROP TABLE IF EXISTS dbo.Dim_Publishers;
END;
GO

-- ==============================================================================
-- 2. TWORZENIE PROCEDURY BUDUJĄCEJ I ZASILAJĄCEJ
-- ==============================================================================
CREATE OR ALTER PROCEDURE dbo.usp_BuildAndLoadStarSchema
AS
BEGIN
    SET NOCOUNT ON;

    -- A. TWORZENIE TABEL WYMIARÓW
    PRINT '--- TWORZENIE TABEL ---';

    CREATE TABLE Dim_Game (
        GameKey INT IDENTITY(1,1) PRIMARY KEY,
        AppID INT UNIQUE,
        Name NVARCHAR(1000)
    );

    CREATE TABLE Dim_Date (
        DateKey INT PRIMARY KEY, -- YYYYMMDD
        FullDate DATE,
        Year INT,
        Quarter INT,
        Month INT,
        MonthName NVARCHAR(20)
    );

    CREATE TABLE Dim_Platform (
        PlatformKey INT IDENTITY(1,1) PRIMARY KEY,
        PlatformName NVARCHAR(100)
    );

    CREATE TABLE Dim_AgeRating (
        AgeKey INT IDENTITY(1,1) PRIMARY KEY,
        RequiredAge INT,
        AgeCategory NVARCHAR(50)
    );

    CREATE TABLE Dim_SupportLevel (
        SupportKey INT IDENTITY(1,1) PRIMARY KEY,
        HasWebsite BIT,
        HasSupport BIT,
        SupportDescription NVARCHAR(100)
    );

    CREATE TABLE Dim_ContentStats (
        ContentKey INT IDENTITY(1,1) PRIMARY KEY,
        AchievementsCount INT,
        AchievementsTier NVARCHAR(50)
    );

    -- Denormalizowane wymiary opisowe (zgodnie z życzeniem bez mostków dla prostoty diagramu)
    CREATE TABLE Dim_Genres (GenreKey INT IDENTITY(1,1) PRIMARY KEY, GenreList NVARCHAR(MAX));
    CREATE TABLE Dim_Publishers (PublisherKey INT IDENTITY(1,1) PRIMARY KEY, PublisherList NVARCHAR(MAX));
    CREATE TABLE Dim_Language (LanguageKey INT IDENTITY(1,1) PRIMARY KEY, LanguageList NVARCHAR(MAX));

    -- B. TWORZENIE TABELI FAKTÓW (Serce gwiazdy)
    CREATE TABLE Fact_GameMetrics (
        FactKey INT IDENTITY(1,1) PRIMARY KEY,
        GameKey INT FOREIGN KEY REFERENCES Dim_Game(GameKey),
        DateKey INT FOREIGN KEY REFERENCES Dim_Date(DateKey),
        PlatformKey INT FOREIGN KEY REFERENCES Dim_Platform(PlatformKey),
        AgeKey INT FOREIGN KEY REFERENCES Dim_AgeRating(AgeKey),
        SupportKey INT FOREIGN KEY REFERENCES Dim_SupportLevel(SupportKey),
        ContentKey INT FOREIGN KEY REFERENCES Dim_ContentStats(ContentKey),
        GenreKey INT FOREIGN KEY REFERENCES Dim_Genres(GenreKey),
        PublisherKey INT FOREIGN KEY REFERENCES Dim_Publishers(PublisherKey),
        LanguageKey INT FOREIGN KEY REFERENCES Dim_Language(LanguageKey),
        
        -- Miary (Metrics)
        Price DECIMAL(10,2),
        MetacriticScore INT,
        UserScore INT,
        PositiveReviews INT,
        NegativeReviews INT,
        PeakCCU INT,
        PlaytimeForever INT
    );

    -- C. ZASILANIE DANYCH (ETL)
    PRINT '--- ZASILANIE DANYCH ---';

    -- Wypełnianie wymiarów słownikowych ze Stagingu
    INSERT INTO Dim_Game (AppID, Name) 
    SELECT DISTINCT TRY_CAST(AppID AS INT), Name FROM stg_SteamGames WHERE TRY_CAST(AppID AS INT) IS NOT NULL;

    INSERT INTO Dim_Platform (PlatformName) 
    SELECT DISTINCT ISNULL(NULLIF(PlatformName, ''), 'Brak danych') FROM (
        SELECT CASE WHEN Windows='True' THEN 'Win ' ELSE '' END + CASE WHEN Mac='True' THEN 'Mac ' ELSE '' END + CASE WHEN Linux='True' THEN 'Lin' ELSE '' END as PlatformName 
        FROM stg_SteamGames
    ) t;

    INSERT INTO Dim_AgeRating (RequiredAge, AgeCategory)
    SELECT DISTINCT TRY_CAST([Required age] AS INT), 
           CASE WHEN TRY_CAST([Required age] AS INT) = 0 THEN 'Dla wszystkich'
                WHEN TRY_CAST([Required age] AS INT) < 13 THEN '7+'
                WHEN TRY_CAST([Required age] AS INT) < 17 THEN '13+'
                ELSE '18+' END
    FROM stg_SteamGames;

    INSERT INTO Dim_Date (DateKey, FullDate, Year, Quarter, Month, MonthName)
    SELECT DISTINCT 
        CAST(FORMAT(TRY_CAST([Release date] AS DATE), 'yyyyMMdd') AS INT),
        TRY_CAST([Release date] AS DATE),
        YEAR(TRY_CAST([Release date] AS DATE)),
        DATEPART(qq, TRY_CAST([Release date] AS DATE)),
        MONTH(TRY_CAST([Release date] AS DATE)),
        DATENAME(mm, TRY_CAST([Release date] AS DATE))
    FROM stg_SteamGames WHERE TRY_CAST([Release date] AS DATE) IS NOT NULL;

    -- Dodanie rekordu technicznego dla braku daty
    INSERT INTO Dim_Date (DateKey, FullDate, Year, Quarter, Month, MonthName) VALUES (-1, NULL, NULL, NULL, NULL, 'N/A');

    INSERT INTO Dim_SupportLevel (HasWebsite, HasSupport, SupportDescription)
    SELECT DISTINCT CAST([Has Website] AS BIT), CAST([Has Support] AS BIT),
           CASE WHEN [Has Website] = 1 AND [Has Support] = 1 THEN 'Pełne wsparcie'
                WHEN [Has Website] = 1 OR [Has Support] = 1 THEN 'Częściowe wsparcie'
                ELSE 'Brak danych kontaktowych' END
    FROM stg_SteamGames;

    INSERT INTO Dim_ContentStats (AchievementsCount, AchievementsTier)
    SELECT DISTINCT TRY_CAST(Achievements AS INT),
           CASE WHEN TRY_CAST(Achievements AS INT) = 0 THEN 'Brak'
                WHEN TRY_CAST(Achievements AS INT) < 10 THEN 'Mało'
                WHEN TRY_CAST(Achievements AS INT) < 50 THEN 'Średnio'
                ELSE 'Bardzo dużo' END
    FROM stg_SteamGames;

    INSERT INTO Dim_Genres (GenreList) SELECT DISTINCT Genres FROM stg_SteamGames;
    INSERT INTO Dim_Publishers (PublisherList) SELECT DISTINCT Publishers FROM stg_SteamGames;
    INSERT INTO Dim_Language (LanguageList) SELECT DISTINCT Languages FROM stg_SteamGames;

    -- D. ZASILANIE TABELI FAKTÓW
    INSERT INTO Fact_GameMetrics (
        GameKey, DateKey, PlatformKey, AgeKey, SupportKey, ContentKey, GenreKey, PublisherKey, LanguageKey,
        Price, MetacriticScore, UserScore, PositiveReviews, NegativeReviews, PeakCCU, PlaytimeForever
    )
    SELECT 
        dg.GameKey,
        ISNULL(CAST(FORMAT(TRY_CAST(stg.[Release date] AS DATE), 'yyyyMMdd') AS INT), -1),
        dp.PlatformKey,
        dar.AgeKey,
        dsl.SupportKey,
        dcs.ContentKey,
        dgn.GenreKey,
        dpb.PublisherKey,
        dlg.LanguageKey,
        TRY_CAST(stg.Price AS DECIMAL(10,2)),
        TRY_CAST(stg.[Metacritic score] AS INT),
        TRY_CAST(stg.[User score] AS INT),
        TRY_CAST(stg.Positive AS INT),
        TRY_CAST(stg.Negative AS INT),
        TRY_CAST(stg.[Peak CCU] AS INT),
        TRY_CAST(stg.[Playtime forever] AS INT)
    FROM stg_SteamGames stg
    JOIN Dim_Game dg ON dg.AppID = TRY_CAST(stg.AppID AS INT)
    JOIN Dim_Platform dp ON dp.PlatformName = (CASE WHEN stg.Windows='True' THEN 'Win ' ELSE '' END + CASE WHEN stg.Mac='True' THEN 'Mac ' ELSE '' END + CASE WHEN stg.Linux='True' THEN 'Lin' ELSE '' END)
    JOIN Dim_AgeRating dar ON dar.RequiredAge = TRY_CAST(stg.[Required age] AS INT)
    JOIN Dim_SupportLevel dsl ON dsl.HasWebsite = CAST(stg.[Has Website] AS BIT) AND dsl.HasSupport = CAST(stg.[Has Support] AS BIT)
    JOIN Dim_ContentStats dcs ON dcs.AchievementsCount = TRY_CAST(stg.Achievements AS INT)
    JOIN Dim_Genres dgn ON ISNULL(dgn.GenreList, '') = ISNULL(stg.Genres, '')
    JOIN Dim_Publishers dpb ON ISNULL(dpb.PublisherList, '') = ISNULL(stg.Publishers, '')
    JOIN Dim_Language dlg ON ISNULL(dlg.LanguageList, '') = ISNULL(stg.Languages, '')

    PRINT '--- SCHEMAT GWIAZDY GOTOWY (9 WYMIARÓW) ---';
END;
GO

-- ==============================================================================
-- 3. URUCHOMIENIE PROCESU
-- ==============================================================================
EXEC dbo.usp_CleanStarSchema;
GO
EXEC dbo.usp_BuildAndLoadStarSchema;
GO