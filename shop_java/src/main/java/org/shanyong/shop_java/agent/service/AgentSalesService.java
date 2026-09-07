package org.shanyong.shop_java.agent.service;

import org.shanyong.shop_java.agent.dto.AgentDailySalesDTO;
import org.shanyong.shop_java.agent.dto.AgentProductSalesDTO;
import org.shanyong.shop_java.agent.dto.AgentSalesOrderDTO;
import org.shanyong.shop_java.agent.dto.AgentSalesSummaryDTO;

import java.time.LocalDate;
import java.util.List;

public interface AgentSalesService {

    AgentSalesSummaryDTO getSalesSummary(LocalDate startDate, LocalDate endDate);

    List<AgentDailySalesDTO> getDailySales(LocalDate startDate, LocalDate endDate);

    List<AgentProductSalesDTO> getTopProducts(LocalDate startDate, LocalDate endDate, Integer limit);

    List<AgentSalesOrderDTO> getRecentPaidOrders(Integer limit);
}
