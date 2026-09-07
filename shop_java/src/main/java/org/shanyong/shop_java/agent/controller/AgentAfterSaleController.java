package org.shanyong.shop_java.agent.controller;


import org.shanyong.shop_java.agent.dto.AgentRefundCategoryStatsResponse;
import org.shanyong.shop_java.agent.dto.AgentRefundProductStatsResponse;
import org.shanyong.shop_java.agent.service.AgentAfterSaleService;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;

@Validated
@RestController
@RequestMapping("/api/agent/after-sale")
public class AgentAfterSaleController {

    private final AgentAfterSaleService agentAfterSaleService;

    public AgentAfterSaleController(AgentAfterSaleService agentAfterSaleService) {
        this.agentAfterSaleService = agentAfterSaleService;
    }

    @GetMapping("/refund-rate/products/recent")
    public ResponseEntity<AgentRefundProductStatsResponse> getRecentProductRefundRates(
        @RequestParam(defaultValue = "30") @Min(value = 1, message = "validation failed")
        @Max(value = 365, message = "validation failed") Integer days,
        @RequestParam(defaultValue = "10") @Min(value = 1, message = "validation failed")
        @Max(value = 50, message = "validation failed") Integer limit
    ) {
        return ResponseEntity.ok(agentAfterSaleService.getRecentProductRefundRates(days, limit));
    }

    @GetMapping("/refund-rate/categories/recent")
    public ResponseEntity<AgentRefundCategoryStatsResponse> getRecentCategoryRefundRates(
        @RequestParam(defaultValue = "30") @Min(value = 1, message = "validation failed")
        @Max(value = 365, message = "validation failed") Integer days,
        @RequestParam(defaultValue = "10") @Min(value = 1, message = "validation failed")
        @Max(value = 50, message = "validation failed") Integer limit
    ) {
        return ResponseEntity.ok(agentAfterSaleService.getRecentCategoryRefundRates(days, limit));
    }
}
