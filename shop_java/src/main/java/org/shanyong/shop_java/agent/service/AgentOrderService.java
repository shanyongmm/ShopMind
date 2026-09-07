package org.shanyong.shop_java.agent.service;

import org.shanyong.shop_java.agent.dto.AgentRecentOrderStatsDTO;
import org.shanyong.shop_java.agent.dto.OrderDTO;

import java.util.List;

public interface AgentOrderService {

    List<OrderDTO> getUserOrders(Long userId);

    OrderDTO getOrderById(Long orderId);

    AgentRecentOrderStatsDTO getRecentOrderStats(Integer days);
}
