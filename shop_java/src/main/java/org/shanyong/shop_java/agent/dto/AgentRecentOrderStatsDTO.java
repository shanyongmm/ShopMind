package org.shanyong.shop_java.agent.dto;

import lombok.Data;

import java.time.LocalDate;

@Data
public class AgentRecentOrderStatsDTO {

    private Integer days;

    private LocalDate startDate;

    private LocalDate endDate;

    private Long orderCount;

    private Double totalOrderAmount;

    private Long paidOrderCount;

    private Double transactionAmount;

    private Double averageTransactionAmount;

    private Boolean hasOrders;

    private Boolean hasPaidOrders;
}
