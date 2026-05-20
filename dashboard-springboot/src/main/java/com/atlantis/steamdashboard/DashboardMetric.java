package com.atlantis.steamdashboard;

import java.math.BigDecimal;

public record DashboardMetric(
        int gameCount,
        BigDecimal averagePrice,
        BigDecimal averageMetacritic,
        long peakCcu
) {
}

