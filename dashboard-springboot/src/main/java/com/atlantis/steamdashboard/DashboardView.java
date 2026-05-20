package com.atlantis.steamdashboard;

import java.util.List;

public record DashboardView(
        DashboardMetric metrics,
        DashboardOptions options,
        List<ChartPoint> trend,
        List<ChartPoint> genres,
        List<ChartPoint> ageDistribution,
        List<ChartPoint> platformDistribution,
        List<ChartPoint> supportDistribution
) {
}

