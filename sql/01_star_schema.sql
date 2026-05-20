USE db_dw_project_steam;
GO

CREATE OR ALTER PROCEDURE dbo.usp_CleanStarSchema
AS
BEGIN
    SET NOCOUNT ON;

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

CREATE OR ALTER PROCEDURE dbo.usp_BuildAndLoadStarSchema
AS
BEGIN
    SET NOCOUNT ON;

    CREATE TABLE dbo.Dim_Game (
        GameKey INT IDENTITY(1,1) PRIMARY KEY,
        AppID INT NOT NULL UNIQUE,
        Name NVARCHAR(1000) NOT NULL
    );

    CREATE TABLE dbo.Dim_Date (
        DateKey INT PRIMARY KEY,
        FullDate DATE NULL,
        Year INT NULL,
        Quarter INT NULL,
        Month INT NULL,
        MonthName NVARCHAR(20) NOT NULL
    );

    CREATE TABLE dbo.Dim_Platform (
        PlatformKey INT IDENTITY(1,1) PRIMARY KEY,
        PlatformName NVARCHAR(100) NOT NULL UNIQUE
    );

    CREATE TABLE dbo.Dim_AgeRating (
        AgeKey INT IDENTITY(1,1) PRIMARY KEY,
        RequiredAge INT NOT NULL,
        AgeCategory NVARCHAR(50) NOT NULL
    );

    CREATE TABLE dbo.Dim_SupportLevel (
        SupportKey INT IDENTITY(1,1) PRIMARY KEY,
        HasWebsite BIT NOT NULL,
        HasSupport BIT NOT NULL,
        SupportDescription NVARCHAR(100) NOT NULL
    );

    CREATE TABLE dbo.Dim_ContentStats (
        ContentKey INT IDENTITY(1,1) PRIMARY KEY,
        AchievementsCount INT NOT NULL,
        AchievementsTier NVARCHAR(50) NOT NULL
    );

    CREATE TABLE dbo.Dim_Genres (
        GenreKey INT IDENTITY(1,1) PRIMARY KEY,
        GenreList NVARCHAR(MAX) NOT NULL
    );

    CREATE TABLE dbo.Dim_Publishers (
        PublisherKey INT IDENTITY(1,1) PRIMARY KEY,
        PublisherList NVARCHAR(MAX) NOT NULL
    );

    CREATE TABLE dbo.Dim_Language (
        LanguageKey INT IDENTITY(1,1) PRIMARY KEY,
        LanguageList NVARCHAR(MAX) NOT NULL
    );

    CREATE TABLE dbo.Fact_GameMetrics (
        FactKey INT IDENTITY(1,1) PRIMARY KEY,
        GameKey INT NOT NULL FOREIGN KEY REFERENCES dbo.Dim_Game(GameKey),
        DateKey INT NOT NULL FOREIGN KEY REFERENCES dbo.Dim_Date(DateKey),
        PlatformKey INT NOT NULL FOREIGN KEY REFERENCES dbo.Dim_Platform(PlatformKey),
        AgeKey INT NOT NULL FOREIGN KEY REFERENCES dbo.Dim_AgeRating(AgeKey),
        SupportKey INT NOT NULL FOREIGN KEY REFERENCES dbo.Dim_SupportLevel(SupportKey),
        ContentKey INT NOT NULL FOREIGN KEY REFERENCES dbo.Dim_ContentStats(ContentKey),
        GenreKey INT NOT NULL FOREIGN KEY REFERENCES dbo.Dim_Genres(GenreKey),
        PublisherKey INT NOT NULL FOREIGN KEY REFERENCES dbo.Dim_Publishers(PublisherKey),
        LanguageKey INT NOT NULL FOREIGN KEY REFERENCES dbo.Dim_Language(LanguageKey),
        Price DECIMAL(10,2) NULL,
        MetacriticScore INT NULL,
        UserScore INT NULL,
        PositiveReviews INT NULL,
        NegativeReviews INT NULL,
        PeakCCU INT NULL,
        PlaytimeForever INT NULL
    );

    WITH CleanStaging AS (
        SELECT
            TRY_CAST(AppID AS INT) AS AppID,
            NULLIF(LTRIM(RTRIM(Name)), '') AS Name,
            TRY_CAST([Release date] AS DATE) AS ReleaseDate,
            TRY_CAST(Price AS DECIMAL(10,2)) AS Price,
            ISNULL(TRY_CAST([Required age] AS INT), 0) AS RequiredAge,
            CASE
                WHEN NULLIF(CONCAT(
                    CASE WHEN Windows = 'True' THEN 'Win ' ELSE '' END,
                    CASE WHEN Mac = 'True' THEN 'Mac ' ELSE '' END,
                    CASE WHEN Linux = 'True' THEN 'Lin' ELSE '' END
                ), '') IS NULL THEN 'Brak danych'
                ELSE RTRIM(CONCAT(
                    CASE WHEN Windows = 'True' THEN 'Win ' ELSE '' END,
                    CASE WHEN Mac = 'True' THEN 'Mac ' ELSE '' END,
                    CASE WHEN Linux = 'True' THEN 'Lin' ELSE '' END
                ))
            END AS PlatformName,
            ISNULL(TRY_CAST([Metacritic score] AS INT), 0) AS MetacriticScore,
            ISNULL(TRY_CAST([User score] AS INT), 0) AS UserScore,
            ISNULL(TRY_CAST(Positive AS INT), 0) AS PositiveReviews,
            ISNULL(TRY_CAST(Negative AS INT), 0) AS NegativeReviews,
            ISNULL(TRY_CAST(Achievements AS INT), 0) AS AchievementsCount,
            ISNULL(TRY_CAST([Peak CCU] AS INT), 0) AS PeakCCU,
            ISNULL(TRY_CAST([Playtime forever] AS INT), 0) AS PlaytimeForever,
            ISNULL(NULLIF(Genres, ''), 'Brak danych') AS Genres,
            ISNULL(NULLIF(Publishers, ''), 'Brak danych') AS Publishers,
            ISNULL(NULLIF(Languages, ''), 'Brak danych') AS Languages,
            ISNULL(TRY_CAST([Has Website] AS BIT), 0) AS HasWebsite,
            ISNULL(TRY_CAST([Has Support] AS BIT), 0) AS HasSupport
        FROM dbo.stg_SteamGames
        WHERE TRY_CAST(AppID AS INT) IS NOT NULL
    )
    SELECT * INTO #CleanStaging FROM CleanStaging;

    INSERT INTO dbo.Dim_Game (AppID, Name)
    SELECT AppID, MAX(ISNULL(Name, CONCAT('Unknown ', AppID)))
    FROM #CleanStaging
    GROUP BY AppID;

    INSERT INTO dbo.Dim_Date (DateKey, FullDate, Year, Quarter, Month, MonthName)
    SELECT DISTINCT
        CAST(FORMAT(ReleaseDate, 'yyyyMMdd') AS INT),
        ReleaseDate,
        YEAR(ReleaseDate),
        DATEPART(QUARTER, ReleaseDate),
        MONTH(ReleaseDate),
        DATENAME(MONTH, ReleaseDate)
    FROM #CleanStaging
    WHERE ReleaseDate IS NOT NULL;

    INSERT INTO dbo.Dim_Date (DateKey, FullDate, Year, Quarter, Month, MonthName)
    VALUES (-1, NULL, NULL, NULL, NULL, 'N/A');

    INSERT INTO dbo.Dim_Platform (PlatformName)
    SELECT DISTINCT PlatformName FROM #CleanStaging;

    INSERT INTO dbo.Dim_AgeRating (RequiredAge, AgeCategory)
    SELECT DISTINCT RequiredAge,
        CASE
            WHEN RequiredAge = 0 THEN 'Dla wszystkich'
            WHEN RequiredAge < 13 THEN '7+'
            WHEN RequiredAge < 17 THEN '13+'
            ELSE '18+'
        END
    FROM #CleanStaging;

    INSERT INTO dbo.Dim_SupportLevel (HasWebsite, HasSupport, SupportDescription)
    SELECT DISTINCT HasWebsite, HasSupport,
        CASE
            WHEN HasWebsite = 1 AND HasSupport = 1 THEN 'Pelne wsparcie'
            WHEN HasWebsite = 1 OR HasSupport = 1 THEN 'Czesciowe wsparcie'
            ELSE 'Brak danych kontaktowych'
        END
    FROM #CleanStaging;

    INSERT INTO dbo.Dim_ContentStats (AchievementsCount, AchievementsTier)
    SELECT DISTINCT AchievementsCount,
        CASE
            WHEN AchievementsCount = 0 THEN 'Brak'
            WHEN AchievementsCount < 10 THEN 'Malo'
            WHEN AchievementsCount < 50 THEN 'Srednio'
            ELSE 'Bardzo duzo'
        END
    FROM #CleanStaging;

    INSERT INTO dbo.Dim_Genres (GenreList) SELECT DISTINCT Genres FROM #CleanStaging;
    INSERT INTO dbo.Dim_Publishers (PublisherList) SELECT DISTINCT Publishers FROM #CleanStaging;
    INSERT INTO dbo.Dim_Language (LanguageList) SELECT DISTINCT Languages FROM #CleanStaging;

    INSERT INTO dbo.Fact_GameMetrics (
        GameKey, DateKey, PlatformKey, AgeKey, SupportKey, ContentKey, GenreKey, PublisherKey, LanguageKey,
        Price, MetacriticScore, UserScore, PositiveReviews, NegativeReviews, PeakCCU, PlaytimeForever
    )
    SELECT
        dg.GameKey,
        ISNULL(CAST(FORMAT(cs.ReleaseDate, 'yyyyMMdd') AS INT), -1),
        dp.PlatformKey,
        da.AgeKey,
        ds.SupportKey,
        dc.ContentKey,
        dge.GenreKey,
        dpu.PublisherKey,
        dl.LanguageKey,
        cs.Price,
        cs.MetacriticScore,
        cs.UserScore,
        cs.PositiveReviews,
        cs.NegativeReviews,
        cs.PeakCCU,
        cs.PlaytimeForever
    FROM #CleanStaging cs
    JOIN dbo.Dim_Game dg ON dg.AppID = cs.AppID
    JOIN dbo.Dim_Platform dp ON dp.PlatformName = cs.PlatformName
    JOIN dbo.Dim_AgeRating da ON da.RequiredAge = cs.RequiredAge
    JOIN dbo.Dim_SupportLevel ds ON ds.HasWebsite = cs.HasWebsite AND ds.HasSupport = cs.HasSupport
    JOIN dbo.Dim_ContentStats dc ON dc.AchievementsCount = cs.AchievementsCount
    JOIN dbo.Dim_Genres dge ON dge.GenreList = cs.Genres
    JOIN dbo.Dim_Publishers dpu ON dpu.PublisherList = cs.Publishers
    JOIN dbo.Dim_Language dl ON dl.LanguageList = cs.Languages;
END;
GO

CREATE OR ALTER PROCEDURE dbo.usp_RebuildSteamWarehouse
AS
BEGIN
    SET NOCOUNT ON;
    EXEC dbo.usp_CleanStarSchema;
    EXEC dbo.usp_BuildAndLoadStarSchema;
END;
GO

CREATE OR ALTER PROCEDURE dbo.usp_ApplySteamGamesUpdate
AS
BEGIN
    SET NOCOUNT ON;

    IF OBJECT_ID('dbo.stg_SteamGames_Update', 'U') IS NULL
    BEGIN
        THROW 50001, 'Missing table dbo.stg_SteamGames_Update.', 1;
    END;

    MERGE dbo.stg_SteamGames AS target
    USING dbo.stg_SteamGames_Update AS source
        ON TRY_CAST(target.AppID AS INT) = TRY_CAST(source.AppID AS INT)
    WHEN MATCHED THEN UPDATE SET
        target.Name = source.Name,
        target.[Release date] = source.[Release date],
        target.Price = source.Price,
        target.[Required age] = source.[Required age],
        target.Windows = source.Windows,
        target.Mac = source.Mac,
        target.Linux = source.Linux,
        target.[Metacritic score] = source.[Metacritic score],
        target.[User score] = source.[User score],
        target.Positive = source.Positive,
        target.Negative = source.Negative,
        target.Achievements = source.Achievements,
        target.[Peak CCU] = source.[Peak CCU],
        target.[Playtime forever] = source.[Playtime forever],
        target.Developers = source.Developers,
        target.Publishers = source.Publishers,
        target.Categories = source.Categories,
        target.Genres = source.Genres,
        target.Tags = source.Tags,
        target.Languages = source.Languages,
        target.Website = source.Website,
        target.[Support URL] = source.[Support URL],
        target.[Support Email] = source.[Support Email],
        target.[Estimated owners] = source.[Estimated owners],
        target.[Has Website] = source.[Has Website],
        target.[Has Support] = source.[Has Support]
    WHEN NOT MATCHED BY TARGET THEN INSERT (
        AppID, Name, [Release date], Price, [Required age], Windows, Mac, Linux,
        [Metacritic score], [User score], Positive, Negative, Achievements, [Peak CCU],
        [Playtime forever], Developers, Publishers, Categories, Genres, Tags, Languages,
        Website, [Support URL], [Support Email], [Estimated owners], [Has Website], [Has Support]
    ) VALUES (
        source.AppID, source.Name, source.[Release date], source.Price, source.[Required age], source.Windows, source.Mac, source.Linux,
        source.[Metacritic score], source.[User score], source.Positive, source.Negative, source.Achievements, source.[Peak CCU],
        source.[Playtime forever], source.Developers, source.Publishers, source.Categories, source.Genres, source.Tags, source.Languages,
        source.Website, source.[Support URL], source.[Support Email], source.[Estimated owners], source.[Has Website], source.[Has Support]
    );

    EXEC dbo.usp_RebuildSteamWarehouse;
END;
GO
