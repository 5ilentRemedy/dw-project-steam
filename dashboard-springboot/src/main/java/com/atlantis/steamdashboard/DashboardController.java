package com.atlantis.steamdashboard;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;

import java.util.List;

@Controller
public class DashboardController {
    private final SteamDashboardService service;
    private final ObjectMapper objectMapper;

    public DashboardController(SteamDashboardService service, ObjectMapper objectMapper) {
        this.service = service;
        this.objectMapper = objectMapper;
    }

    @GetMapping("/")
    public String index(
            @RequestParam(required = false) List<Integer> years,
            @RequestParam(required = false) List<String> platforms,
            @RequestParam(required = false) List<String> ages,
            @RequestParam(required = false) List<String> support,
            @RequestParam(required = false) List<String> achievements,
            Model model
    ) throws JsonProcessingException {
        DashboardFilter filter = new DashboardFilter(years, platforms, ages, support, achievements);
        DashboardView view = service.loadDashboard(filter);

        model.addAttribute("view", view);
        model.addAttribute("filter", filter);
        model.addAttribute("trendJson", objectMapper.writeValueAsString(view.trend()));
        model.addAttribute("genresJson", objectMapper.writeValueAsString(view.genres()));
        model.addAttribute("ageJson", objectMapper.writeValueAsString(view.ageDistribution()));
        model.addAttribute("platformJson", objectMapper.writeValueAsString(view.platformDistribution()));
        model.addAttribute("supportJson", objectMapper.writeValueAsString(view.supportDistribution()));
        return "dashboard";
    }
}

