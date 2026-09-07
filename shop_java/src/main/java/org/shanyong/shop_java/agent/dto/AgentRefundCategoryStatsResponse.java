package org.shanyong.shop_java.agent.dto;

import lombok.Data;

import java.time.LocalDate;
import java.util.List;

@Data
public class AgentRefundCategoryStatsResponse {

    private Integer days;

    private LocalDate startDate;

    private LocalDate endDate;

    private Boolean hasRefunds;

    private List<AgentRefundCategoryStatsDTO> records;
}
