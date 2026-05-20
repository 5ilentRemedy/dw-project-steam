package com.atlantis.steamdashboard;

import java.util.List;

public record DashboardFilter(
        List<Integer> years,
        List<String> platforms,
        List<String> ages,
        List<String> support,
        List<String> achievements
) {
}

