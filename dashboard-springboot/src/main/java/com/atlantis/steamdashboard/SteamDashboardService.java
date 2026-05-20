package com.atlantis.steamdashboard;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;
import java.util.StringJoiner;

@Service
public class SteamDashboardService {
    private final JdbcTemplate jdbcTemplate;

    public SteamDashboardService(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    public DashboardView loadDashboard(DashboardFilter filter) {
        SqlFilter sqlFilter = buildFilter(filter);
        DashboardMetric metrics = loadMetrics(sqlFilter);
        DashboardOptions options = loadOptions();

        return new DashboardView(
                metrics,
                options,
                loadPoints("""
                        SELECT CAST(dd.Year AS NVARCHAR(20)) AS Label, COUNT(*) AS Value
                        FROM dbo.Fact_GameMetrics f
                        JOIN dbo.Dim_Date dd ON dd.DateKey = f.DateKey
                        JOIN dbo.Dim_Platform dp ON dp.PlatformKey = f.PlatformKey
                        JOIN dbo.Dim_AgeRating da ON da.AgeKey = f.AgeKey
                        JOIN dbo.Dim_SupportLevel ds ON ds.SupportKey = f.SupportKey
                        JOIN dbo.Dim_ContentStats dc ON dc.ContentKey = f.ContentKey
                        WHERE dd.Year IS NOT NULL %s
                        GROUP BY dd.Year
                        ORDER BY dd.Year
                        """.formatted(sqlFilter.where()), sqlFilter.params()),
                loadPoints("""
                        SELECT TOP 10 LTRIM(RTRIM(value)) AS Label, COUNT(*) AS Value
                        FROM dbo.Fact_GameMetrics f
                        JOIN dbo.Dim_Date dd ON dd.DateKey = f.DateKey
                        JOIN dbo.Dim_Platform dp ON dp.PlatformKey = f.PlatformKey
                        JOIN dbo.Dim_AgeRating da ON da.AgeKey = f.AgeKey
                        JOIN dbo.Dim_SupportLevel ds ON ds.SupportKey = f.SupportKey
                        JOIN dbo.Dim_ContentStats dc ON dc.ContentKey = f.ContentKey
                        JOIN dbo.Dim_Genres dg ON dg.GenreKey = f.GenreKey
                        CROSS APPLY STRING_SPLIT(dg.GenreList, ',')
                        WHERE LTRIM(RTRIM(value)) <> '' %s
                        GROUP BY LTRIM(RTRIM(value))
                        ORDER BY COUNT(*) DESC
                        """.formatted(sqlFilter.where()), sqlFilter.params()),
                loadPoints("""
                        SELECT da.AgeCategory AS Label, COUNT(*) AS Value
                        FROM dbo.Fact_GameMetrics f
                        JOIN dbo.Dim_Date dd ON dd.DateKey = f.DateKey
                        JOIN dbo.Dim_Platform dp ON dp.PlatformKey = f.PlatformKey
                        JOIN dbo.Dim_AgeRating da ON da.AgeKey = f.AgeKey
                        JOIN dbo.Dim_SupportLevel ds ON ds.SupportKey = f.SupportKey
                        JOIN dbo.Dim_ContentStats dc ON dc.ContentKey = f.ContentKey
                        WHERE 1 = 1 %s
                        GROUP BY da.AgeCategory
                        ORDER BY COUNT(*) DESC
                        """.formatted(sqlFilter.where()), sqlFilter.params()),
                loadPoints("""
                        SELECT dp.PlatformName AS Label, COUNT(*) AS Value
                        FROM dbo.Fact_GameMetrics f
                        JOIN dbo.Dim_Date dd ON dd.DateKey = f.DateKey
                        JOIN dbo.Dim_Platform dp ON dp.PlatformKey = f.PlatformKey
                        JOIN dbo.Dim_AgeRating da ON da.AgeKey = f.AgeKey
                        JOIN dbo.Dim_SupportLevel ds ON ds.SupportKey = f.SupportKey
                        JOIN dbo.Dim_ContentStats dc ON dc.ContentKey = f.ContentKey
                        WHERE 1 = 1 %s
                        GROUP BY dp.PlatformName
                        ORDER BY COUNT(*) DESC
                        """.formatted(sqlFilter.where()), sqlFilter.params()),
                loadPoints("""
                        SELECT ds.SupportDescription AS Label, COUNT(*) AS Value
                        FROM dbo.Fact_GameMetrics f
                        JOIN dbo.Dim_Date dd ON dd.DateKey = f.DateKey
                        JOIN dbo.Dim_Platform dp ON dp.PlatformKey = f.PlatformKey
                        JOIN dbo.Dim_AgeRating da ON da.AgeKey = f.AgeKey
                        JOIN dbo.Dim_SupportLevel ds ON ds.SupportKey = f.SupportKey
                        JOIN dbo.Dim_ContentStats dc ON dc.ContentKey = f.ContentKey
                        WHERE 1 = 1 %s
                        GROUP BY ds.SupportDescription
                        ORDER BY COUNT(*) DESC
                        """.formatted(sqlFilter.where()), sqlFilter.params())
        );
    }

    private DashboardMetric loadMetrics(SqlFilter filter) {
        return jdbcTemplate.queryForObject("""
                SELECT
                    COUNT(*) AS GameCount,
                    AVG(CAST(f.Price AS DECIMAL(10,2))) AS AveragePrice,
                    AVG(CASE WHEN f.MetacriticScore > 0 THEN CAST(f.MetacriticScore AS DECIMAL(10,2)) END) AS AverageMetacritic,
                    SUM(CAST(f.PeakCCU AS BIGINT)) AS PeakCcu
                FROM dbo.Fact_GameMetrics f
                JOIN dbo.Dim_Date dd ON dd.DateKey = f.DateKey
                JOIN dbo.Dim_Platform dp ON dp.PlatformKey = f.PlatformKey
                JOIN dbo.Dim_AgeRating da ON da.AgeKey = f.AgeKey
                JOIN dbo.Dim_SupportLevel ds ON ds.SupportKey = f.SupportKey
                JOIN dbo.Dim_ContentStats dc ON dc.ContentKey = f.ContentKey
                WHERE 1 = 1 %s
                """.formatted(filter.where()), (rs, rowNum) -> new DashboardMetric(
                rs.getInt("GameCount"),
                valueOrZero(rs.getBigDecimal("AveragePrice")),
                valueOrZero(rs.getBigDecimal("AverageMetacritic")),
                rs.getLong("PeakCcu")
        ), filter.params().toArray());
    }

    private DashboardOptions loadOptions() {
        return new DashboardOptions(
                jdbcTemplate.queryForList("SELECT DISTINCT Year FROM dbo.Dim_Date WHERE Year IS NOT NULL ORDER BY Year DESC", Integer.class),
                jdbcTemplate.queryForList("SELECT PlatformName FROM dbo.Dim_Platform ORDER BY PlatformName", String.class),
                jdbcTemplate.queryForList("SELECT DISTINCT AgeCategory FROM dbo.Dim_AgeRating ORDER BY AgeCategory", String.class),
                jdbcTemplate.queryForList("SELECT DISTINCT SupportDescription FROM dbo.Dim_SupportLevel ORDER BY SupportDescription", String.class),
                jdbcTemplate.queryForList("SELECT DISTINCT AchievementsTier FROM dbo.Dim_ContentStats ORDER BY AchievementsTier", String.class)
        );
    }

    private List<ChartPoint> loadPoints(String sql, List<Object> params) {
        return jdbcTemplate.query(sql, (rs, rowNum) -> new ChartPoint(rs.getString("Label"), rs.getLong("Value")), params.toArray());
    }

    private SqlFilter buildFilter(DashboardFilter filter) {
        StringJoiner where = new StringJoiner(" ");
        List<Object> params = new ArrayList<>();
        addInClause("dd.Year", filter.years(), where, params);
        addInClause("dp.PlatformName", filter.platforms(), where, params);
        addInClause("da.AgeCategory", filter.ages(), where, params);
        addInClause("ds.SupportDescription", filter.support(), where, params);
        addInClause("dc.AchievementsTier", filter.achievements(), where, params);
        String clause = where.length() == 0 ? "" : " AND " + where;
        return new SqlFilter(clause, params);
    }

    private void addInClause(String column, List<?> values, StringJoiner where, List<Object> params) {
        if (values == null || values.isEmpty()) {
            return;
        }
        where.add(column + " IN (" + "?,".repeat(values.size()).replaceAll(",$", "") + ")");
        params.addAll(values);
    }

    private BigDecimal valueOrZero(BigDecimal value) {
        return value == null ? BigDecimal.ZERO : value;
    }

    private record SqlFilter(String where, List<Object> params) {
    }
}

