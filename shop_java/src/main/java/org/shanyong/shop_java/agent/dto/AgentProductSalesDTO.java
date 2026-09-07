package org.shanyong.shop_java.agent.dto;

import lombok.Data;

@Data
public class AgentProductSalesDTO {

    private Long productId;

    private String productName;

    private String sku;

    private Long salesQuantity;

    private Double salesAmount;

    private Long orderCount;
}
