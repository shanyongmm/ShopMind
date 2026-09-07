package org.shanyong.shop_java.agent.dto;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class AgentSalesOrderDTO {

    private Long orderId;

    private String orderNo;

    private Long userId;

    private Integer status;

    private Double totalAmount;

    private Long totalQuantity;

    private LocalDateTime createdAt;

    private LocalDateTime payTime;
}
