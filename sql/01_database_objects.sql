USE db_dw_project_steam;
GO

DROP TABLE IF EXISTS dbo.stg_SteamGames_Update;
DROP TABLE IF EXISTS dbo.stg_SteamGames;
GO

CREATE TABLE dbo.stg_SteamGames (
    AppID NVARCHAR(MAX) NULL,
    Name NVARCHAR(MAX) NULL,
    ReleaseDate NVARCHAR(MAX) NULL,
    Price NVARCHAR(MAX) NULL,
    RequiredAge NVARCHAR(MAX) NULL,
    Windows NVARCHAR(MAX) NULL,
    Mac NVARCHAR(MAX) NULL,
    Linux NVARCHAR(MAX) NULL,
    MetacriticScore NVARCHAR(MAX) NULL,
    UserScore NVARCHAR(MAX) NULL,
    PositiveReviews NVARCHAR(MAX) NULL,
    NegativeReviews NVARCHAR(MAX) NULL,
    Achievements NVARCHAR(MAX) NULL,
    PeakCCU NVARCHAR(MAX) NULL,
    PlaytimeForever NVARCHAR(MAX) NULL,
    Developers NVARCHAR(MAX) NULL,
    Publishers NVARCHAR(MAX) NULL,
    Categories NVARCHAR(MAX) NULL,
    Genres NVARCHAR(MAX) NULL,
    Tags NVARCHAR(MAX) NULL,
    Languages NVARCHAR(MAX) NULL,
    Website NVARCHAR(MAX) NULL,
    SupportUrl NVARCHAR(MAX) NULL,
    SupportEmail NVARCHAR(MAX) NULL,
    EstimatedOwners NVARCHAR(MAX) NULL,
    HasWebsite NVARCHAR(MAX) NULL,
    HasSupport NVARCHAR(MAX) NULL
);
GO

CREATE TABLE dbo.stg_SteamGames_Update (
    AppID NVARCHAR(MAX) NULL,
    Name NVARCHAR(MAX) NULL,
    ReleaseDate NVARCHAR(MAX) NULL,
    Price NVARCHAR(MAX) NULL,
    RequiredAge NVARCHAR(MAX) NULL,
    Windows NVARCHAR(MAX) NULL,
    Mac NVARCHAR(MAX) NULL,
    Linux NVARCHAR(MAX) NULL,
    MetacriticScore NVARCHAR(MAX) NULL,
    UserScore NVARCHAR(MAX) NULL,
    PositiveReviews NVARCHAR(MAX) NULL,
    NegativeReviews NVARCHAR(MAX) NULL,
    Achievements NVARCHAR(MAX) NULL,
    PeakCCU NVARCHAR(MAX) NULL,
    PlaytimeForever NVARCHAR(MAX) NULL,
    Developers NVARCHAR(MAX) NULL,
    Publishers NVARCHAR(MAX) NULL,
    Categories NVARCHAR(MAX) NULL,
    Genres NVARCHAR(MAX) NULL,
    Tags NVARCHAR(MAX) NULL,
    Languages NVARCHAR(MAX) NULL,
    Website NVARCHAR(MAX) NULL,
    SupportUrl NVARCHAR(MAX) NULL,
    SupportEmail NVARCHAR(MAX) NULL,
    EstimatedOwners NVARCHAR(MAX) NULL,
    HasWebsite NVARCHAR(MAX) NULL,
    HasSupport NVARCHAR(MAX) NULL
);
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
    DROP TABLE IF EXISTS dbo.Dim_SupportLevel;
    DROP TABLE IF EXISTS dbo.Dim_ContentStats;
    DROP TABLE IF EXISTS dbo.Dim_Genres;
    DROP TABLE IF EXISTS dbo.Dim_Publishers;
    DROP TABLE IF EXISTS dbo.Dim_Language;
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
            ISNULL(NULLIF(Name, ''), 'Unknown') AS Name,
            TRY_CAST(ReleaseDate AS DATE) AS ReleaseDate,
            ISNULL(TRY_CAST(Price AS DECIMAL(10,2)), 0) AS Price,
            ISNULL(TRY_CAST(RequiredAge AS INT), 0) AS RequiredAge,
            CASE WHEN UPPER(LTRIM(RTRIM(Windows))) IN ('TRUE', '1', 'YES') THEN 1 ELSE 0 END AS HasWindows,
            CASE WHEN UPPER(LTRIM(RTRIM(Mac))) IN ('TRUE', '1', 'YES') THEN 1 ELSE 0 END AS HasMac,
            CASE WHEN UPPER(LTRIM(RTRIM(Linux))) IN ('TRUE', '1', 'YES') THEN 1 ELSE 0 END AS HasLinux,
            ISNULL(TRY_CAST(MetacriticScore AS INT), 0) AS MetacriticScore,
            ISNULL(TRY_CAST(UserScore AS INT), 0) AS UserScore,
            ISNULL(TRY_CAST(PositiveReviews AS INT), 0) AS PositiveReviews,
            ISNULL(TRY_CAST(NegativeReviews AS INT), 0) AS NegativeReviews,
            ISNULL(TRY_CAST(Achievements AS INT), 0) AS AchievementsCount,
            ISNULL(TRY_CAST(PeakCCU AS INT), 0) AS PeakCCU,
            ISNULL(TRY_CAST(PlaytimeForever AS INT), 0) AS PlaytimeForever,
            ISNULL(NULLIF(Genres, ''), 'Unknown') AS Genres,
            ISNULL(NULLIF(Publishers, ''), 'Unknown') AS Publishers,
            ISNULL(NULLIF(Languages, ''), 'Unknown') AS Languages,
            ISNULL(TRY_CAST(HasWebsite AS BIT), 0) AS HasWebsite,
            ISNULL(TRY_CAST(HasSupport AS BIT), 0) AS HasSupport
        FROM dbo.stg_SteamGames
        WHERE TRY_CAST(AppID AS INT) IS NOT NULL
    )
    SELECT * INTO #CleanStaging FROM CleanStaging;

    INSERT INTO dbo.Dim_Game (AppID, Name)
    SELECT AppID, MAX(Name)
    FROM #CleanStaging
    GROUP BY AppID;

    INSERT INTO dbo.Dim_Date (DateKey, FullDate, Year, Quarter, Month, MonthName)
    SELECT DISTINCT
        CAST(CONVERT(CHAR(8), ReleaseDate, 112) AS INT),
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
    SELECT 'Windows'
    UNION ALL SELECT 'Mac'
    UNION ALL SELECT 'Linux'
    UNION ALL SELECT 'Unknown';

    INSERT INTO dbo.Dim_AgeRating (RequiredAge, AgeCategory)
    SELECT DISTINCT RequiredAge,
        CASE
            WHEN RequiredAge = 0 THEN 'All ages'
            WHEN RequiredAge < 13 THEN '7+'
            WHEN RequiredAge < 17 THEN '13+'
            ELSE '18+'
        END
    FROM #CleanStaging;

    INSERT INTO dbo.Dim_SupportLevel (HasWebsite, HasSupport, SupportDescription)
    SELECT DISTINCT HasWebsite, HasSupport,
        CASE
            WHEN HasWebsite = 1 AND HasSupport = 1 THEN 'Website and support'
            WHEN HasWebsite = 1 THEN 'Website only'
            WHEN HasSupport = 1 THEN 'Support only'
            ELSE 'No support data'
        END
    FROM #CleanStaging;

    INSERT INTO dbo.Dim_ContentStats (AchievementsCount, AchievementsTier)
    SELECT DISTINCT AchievementsCount,
        CASE
            WHEN AchievementsCount = 0 THEN 'None'
            WHEN AchievementsCount < 10 THEN 'Low'
            WHEN AchievementsCount < 50 THEN 'Medium'
            ELSE 'High'
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
        ISNULL(CAST(CONVERT(CHAR(8), cs.ReleaseDate, 112) AS INT), -1),
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
    CROSS APPLY (
        SELECT 'Windows' AS PlatformName WHERE cs.HasWindows = 1
        UNION ALL SELECT 'Mac' WHERE cs.HasMac = 1
        UNION ALL SELECT 'Linux' WHERE cs.HasLinux = 1
        UNION ALL SELECT 'Unknown' WHERE cs.HasWindows = 0 AND cs.HasMac = 0 AND cs.HasLinux = 0
    ) platform_rows
    JOIN dbo.Dim_Game dg ON dg.AppID = cs.AppID
    JOIN dbo.Dim_Platform dp ON dp.PlatformName = platform_rows.PlatformName
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

    MERGE dbo.stg_SteamGames AS target
    USING dbo.stg_SteamGames_Update AS source
        ON TRY_CAST(target.AppID AS INT) = TRY_CAST(source.AppID AS INT)
    WHEN MATCHED THEN
        UPDATE SET
            Name = source.Name,
            ReleaseDate = source.ReleaseDate,
            Price = source.Price,
            RequiredAge = source.RequiredAge,
            Windows = source.Windows,
            Mac = source.Mac,
            Linux = source.Linux,
            MetacriticScore = source.MetacriticScore,
            UserScore = source.UserScore,
            PositiveReviews = source.PositiveReviews,
            NegativeReviews = source.NegativeReviews,
            Achievements = source.Achievements,
            PeakCCU = source.PeakCCU,
            PlaytimeForever = source.PlaytimeForever,
            Developers = source.Developers,
            Publishers = source.Publishers,
            Categories = source.Categories,
            Genres = source.Genres,
            Tags = source.Tags,
            Languages = source.Languages,
            Website = source.Website,
            SupportUrl = source.SupportUrl,
            SupportEmail = source.SupportEmail,
            EstimatedOwners = source.EstimatedOwners,
            HasWebsite = source.HasWebsite,
            HasSupport = source.HasSupport
    WHEN NOT MATCHED BY TARGET THEN
        INSERT (
            AppID, Name, ReleaseDate, Price, RequiredAge, Windows, Mac, Linux,
            MetacriticScore, UserScore, PositiveReviews, NegativeReviews, Achievements,
            PeakCCU, PlaytimeForever, Developers, Publishers, Categories, Genres, Tags,
            Languages, Website, SupportUrl, SupportEmail, EstimatedOwners, HasWebsite, HasSupport
        )
        VALUES (
            source.AppID, source.Name, source.ReleaseDate, source.Price, source.RequiredAge, source.Windows, source.Mac, source.Linux,
            source.MetacriticScore, source.UserScore, source.PositiveReviews, source.NegativeReviews, source.Achievements,
            source.PeakCCU, source.PlaytimeForever, source.Developers, source.Publishers, source.Categories, source.Genres, source.Tags,
            source.Languages, source.Website, source.SupportUrl, source.SupportEmail, source.EstimatedOwners, source.HasWebsite, source.HasSupport
        );

    EXEC dbo.usp_RebuildSteamWarehouse;
END;
GO
