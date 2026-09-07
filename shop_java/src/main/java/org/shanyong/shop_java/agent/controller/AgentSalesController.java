package org.shanyong.shop_java.agent.controller;


import org.shanyong.shop_java.agent.dto.AgentDailySalesDTO;
import org.shanyong.shop_java.agent.dto.AgentProductSalesDTO;
import org.shanyong.shop_java.agent.dto.AgentSalesOrderDTO;
import org.shanyong.shop_java.agent.dto.AgentSalesSummaryDTO;
import org.shanyong.shop_java.agent.service.AgentSalesService;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import java.time.LocalDate;
import java.util.List;

@Validated
@RestController
@RequestMapping("/api/agent/sales")
public class AgentSalesController {

    private final AgentSalesService agentSalesService;

    public AgentSalesController(AgentSalesService agentSalesService) {
        this.agentSalesService = agentSalesService;
    }

    @GetMapping("/summary")
    public ResponseEntity<AgentSalesSummaryDTO> getSalesSummary(
        @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate startDate,
        @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate endDate
    ) {
        return ResponseEntity.ok(agentSalesService.getSalesSummary(startDate, endDate));
    }

    @GetMapping("/daily")
    public ResponseEntity<List<AgentDailySalesDTO>> getDailySales(
        @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate startDate,
        @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate endDate
    ) {
        return ResponseEntity.ok(agentSalesService.getDailySales(startDate, endDate));
    }

    @GetMapping("/top-products")
    public ResponseEntity<List<AgentProductSalesDTO>> getTopProducts(
        @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate startDate,
        @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate endDate,
        @RequestParam(defaultValue = "10") @Min(value = 1, message = "validation failed")
        @Max(value = 50, message = "validation failed") Integer limit
    ) {
        return ResponseEntity.ok(agentSalesService.getTopProducts(startDate, endDate, limit));
    }

    @GetMapping("/recent-orders")
    public ResponseEntity<List<AgentSalesOrderDTO>> getRecentPaidOrders(
        @RequestParam(defaultValue = "10") @Min(value = 1, message = "validation failed")
        @Max(value = 50, message = "validation failed") Integer limit
    ) {
        return ResponseEntity.ok(agentSalesService.getRecentPaidOrders(limit));
    }
}
