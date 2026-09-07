package org.shanyong.shop_java.agent.service.impl;

import org.shanyong.shop_java.agent.dto.AgentDailySalesDTO;
import org.shanyong.shop_java.agent.dto.AgentProductSalesDTO;
import org.shanyong.shop_java.agent.dto.AgentSalesOrderDTO;
import org.shanyong.shop_java.agent.dto.AgentSalesSummaryDTO;
import org.shanyong.shop_java.agent.repository.AgentSalesRepository;
import org.shanyong.shop_java.agent.service.AgentSalesService;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;

@Service
public class AgentSalesServiceImpl implements AgentSalesService {

    private final AgentSalesRepository agentSalesRepository;

    public AgentSalesServiceImpl(AgentSalesRepository agentSalesRepository) {
        this.agentSalesRepository = agentSalesRepository;
    }

    @Override
    @Transactional(readOnly = true)
    public AgentSalesSummaryDTO getSalesSummary(LocalDate startDate, LocalDate endDate) {
        DateRange dateRange = resolveDateRange(startDate, endDate);
        AgentSalesSummaryDTO summary = agentSalesRepository.selectSalesSummary(
            dateRange.startTime(),
            dateRange.endTime()
        );
        return normalizeSummary(summary);
    }

    @Override
    @Transactional(readOnly = true)
    public List<AgentDailySalesDTO> getDailySales(LocalDate startDate, LocalDate endDate) {
        DateRange dateRange = resolveDateRange(startDate, endDate);
        return agentSalesRepository.selectDailySales(dateRange.startTime(), dateRange.endTime());
    }

    @Override
    @Transactional(readOnly = true)
    public List<AgentProductSalesDTO> getTopProducts(LocalDate startDate, LocalDate endDate, Integer limit) {
        DateRange dateRange = resolveDateRange(startDate, endDate);
        return agentSalesRepository.selectTopProducts(dateRange.startTime(), dateRange.endTime(), limit);
    }

    @Override
    @Transactional(readOnly = true)
    public List<AgentSalesOrderDTO> getRecentPaidOrders(Integer limit) {
        return agentSalesRepository.selectRecentPaidOrders(limit);
    }

    private DateRange resolveDateRange(LocalDate startDate, LocalDate endDate) {
        if (startDate != null && endDate != null && endDate.isBefore(startDate)) {
            throw new RuntimeException("SALES_DATE_RANGE_INVALID");
        }
        LocalDateTime startTime = startDate == null ? null : startDate.atStartOfDay();
        LocalDateTime endTime = endDate == null ? null : endDate.plusDays(1).atStartOfDay();
        return new DateRange(startTime, endTime);
    }

    private AgentSalesSummaryDTO normalizeSummary(AgentSalesSummaryDTO summary) {
        AgentSalesSummaryDTO normalized = summary == null ? new AgentSalesSummaryDTO() : summary;
        if (normalized.getOrderCount() == null) {
            normalized.setOrderCount(0L);
        }
        if (normalized.getTotalAmount() == null) {
            normalized.setTotalAmount(0D);
        }
        if (normalized.getTotalQuantity() == null) {
            normalized.setTotalQuantity(0L);
        }
        if (normalized.getAverageOrderAmount() == null) {
            normalized.setAverageOrderAmount(0D);
        }
        return normalized;
    }

    private record DateRange(LocalDateTime startTime, LocalDateTime endTime) {
    }
}
