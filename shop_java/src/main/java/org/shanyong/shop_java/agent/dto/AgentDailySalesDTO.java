package org.shanyong.shop_java.agent.dto;

import lombok.Data;

@Data
public class AgentDailySalesDTO {

    private String saleDate;

    private Long orderCount;

    private Long salesQuantity;

    private Double salesAmount;
}
