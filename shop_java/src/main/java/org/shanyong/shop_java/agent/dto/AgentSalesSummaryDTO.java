package org.shanyong.shop_java.agent.dto;

import lombok.Data;

@Data
public class AgentSalesSummaryDTO {

    private Long orderCount;

    private Double totalAmount;

    private Long totalQuantity;

    private Double averageOrderAmount;
}
