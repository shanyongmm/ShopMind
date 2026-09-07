package org.shanyong.shop_java.agent.service;


import org.shanyong.shop_java.agent.dto.AgentRefundCategoryStatsResponse;
import org.shanyong.shop_java.agent.dto.AgentRefundProductStatsResponse;

public interface AgentAfterSaleService {

    AgentRefundProductStatsResponse getRecentProductRefundRates(Integer days, Integer limit);

    AgentRefundCategoryStatsResponse getRecentCategoryRefundRates(Integer days, Integer limit);
}
