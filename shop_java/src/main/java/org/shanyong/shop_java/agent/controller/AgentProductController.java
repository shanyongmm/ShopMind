package org.shanyong.shop_java.agent.controller;


import org.shanyong.shop_java.agent.entity.Product;
import org.shanyong.shop_java.agent.service.AgentProductService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import java.util.List;

@Validated
@RestController
@RequestMapping("/api/agent/product")
public class AgentProductController {
    @Autowired
    private AgentProductService agentProductService;

    @GetMapping("/{id}")
    public Product getProductById(@PathVariable int id) {
        return agentProductService.getProductById(id);
    }

    @GetMapping("/list")
    public List<Product> getAllProductOrderBySalesCount() {
        return agentProductService.getAllProductOrderBySalesCount();
    }

    @GetMapping("/hot")
    public List<Product> getHotProducts(
        @RequestParam(defaultValue = "10") @Min(value = 1, message = "validation failed")
        @Max(value = 50, message = "validation failed") Integer limit
    ) {
        return agentProductService.getHotProducts(limit);
    }

    @GetMapping("/recommended")
    public List<Product> getRecommendedProducts(
        @RequestParam(required = false) String keyword,
        @RequestParam(defaultValue = "10") @Min(value = 1, message = "validation failed")
        @Max(value = 50, message = "validation failed") Integer limit
    ) {
        return agentProductService.getRecommendedProducts(keyword, limit);
    }
}
