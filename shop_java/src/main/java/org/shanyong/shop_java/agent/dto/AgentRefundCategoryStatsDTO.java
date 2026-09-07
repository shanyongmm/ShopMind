package org.shanyong.shop_java.agent.dto;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class AgentRefundCategoryStatsDTO {

    private Long categoryId;

    private String categoryName;

    private Long soldQuantity;

    private Long refundQuantity;

    private Long refundRequestCount;

    private Double refundAmount;

    private Double refundRate;

    private LocalDateTime latestApplyTime;
}
