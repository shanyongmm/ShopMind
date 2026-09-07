package org.shanyong.shop_java.agent.controller;


import org.shanyong.shop_java.agent.dto.AgentRecentOrderStatsDTO;
import org.shanyong.shop_java.agent.dto.OrderDTO;
import org.shanyong.shop_java.agent.service.AgentOrderService;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.Positive;
import java.util.List;

@Validated
@RestController
@RequestMapping("/api/agent/order")
public class AgentOrderController {

    private final AgentOrderService agentOrderService;

    public AgentOrderController(AgentOrderService agentOrderService) {
        this.agentOrderService = agentOrderService;
    }

    @GetMapping("/user/{userId}")
    public ResponseEntity<List<OrderDTO>> getUserOrders(
        @PathVariable @Positive(message = "validation failed") Long userId
    ) {
        return ResponseEntity.ok(agentOrderService.getUserOrders(userId));
    }

    @GetMapping("/{orderId}")
    public ResponseEntity<OrderDTO> getOrderById(
        @PathVariable @Positive(message = "validation failed") Long orderId
    ) {
        return ResponseEntity.ok(agentOrderService.getOrderById(orderId));
    }

    @GetMapping("/stats/recent")
    public ResponseEntity<AgentRecentOrderStatsDTO> getRecentOrderStats(
        @RequestParam(defaultValue = "7") @Min(value = 1, message = "validation failed")
        @Max(value = 365, message = "validation failed") Integer days
    ) {
        return ResponseEntity.ok(agentOrderService.getRecentOrderStats(days));
    }
}
