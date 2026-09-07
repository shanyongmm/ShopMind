package org.shanyong.shop_java.agent.service.impl;

import org.shanyong.shop_java.agent.dto.AgentRecentOrderStatsDTO;
import org.shanyong.shop_java.agent.dto.OrderDTO;
import org.shanyong.shop_java.agent.repository.AgentOrderRepository;
import org.shanyong.shop_java.agent.repository.AgentOrderStatsRepository;
import org.shanyong.shop_java.agent.service.AgentOrderService;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;

@Service
public class AgentOrderServiceImpl implements AgentOrderService {

    private final AgentOrderRepository agentOrderRepository;
    private final AgentOrderStatsRepository agentOrderStatsRepository;

    public AgentOrderServiceImpl(
        AgentOrderRepository agentOrderRepository,
        AgentOrderStatsRepository agentOrderStatsRepository
    ) {
        this.agentOrderRepository = agentOrderRepository;
        this.agentOrderStatsRepository = agentOrderStatsRepository;
    }

    @Override
    public List<OrderDTO> getUserOrders(Long userId) {
        return agentOrderRepository.selectByUserId(userId);
    }

    @Override
    public OrderDTO getOrderById(Long orderId) {
        return agentOrderRepository.selectById(orderId);
    }

    @Override
    public AgentRecentOrderStatsDTO getRecentOrderStats(Integer days) {
        int normalizedDays = days == null ? 7 : days;
        LocalDate endDate = LocalDate.now();
        LocalDate startDate = endDate.minusDays(normalizedDays - 1L);
        LocalDateTime startTime = startDate.atStartOfDay();
        LocalDateTime endTime = endDate.plusDays(1).atStartOfDay();

        AgentRecentOrderStatsDTO stats = agentOrderStatsRepository.selectRecentOrderStats(startTime, endTime);
        return normalizeStats(stats, normalizedDays, startDate, endDate);
    }

    private AgentRecentOrderStatsDTO normalizeStats(
        AgentRecentOrderStatsDTO stats,
        Integer days,
        LocalDate startDate,
        LocalDate endDate
    ) {
        AgentRecentOrderStatsDTO normalized = stats == null ? new AgentRecentOrderStatsDTO() : stats;
        normalized.setDays(days);
        normalized.setStartDate(startDate);
        normalized.setEndDate(endDate);
        if (normalized.getOrderCount() == null) {
            normalized.setOrderCount(0L);
        }
        if (normalized.getTotalOrderAmount() == null) {
            normalized.setTotalOrderAmount(0D);
        }
        if (normalized.getPaidOrderCount() == null) {
            normalized.setPaidOrderCount(0L);
        }
        if (normalized.getTransactionAmount() == null) {
            normalized.setTransactionAmount(0D);
        }
        if (normalized.getAverageTransactionAmount() == null) {
            normalized.setAverageTransactionAmount(0D);
        }
        normalized.setHasOrders(normalized.getOrderCount() > 0);
        normalized.setHasPaidOrders(normalized.getPaidOrderCount() > 0);
        return normalized;
    }
}
