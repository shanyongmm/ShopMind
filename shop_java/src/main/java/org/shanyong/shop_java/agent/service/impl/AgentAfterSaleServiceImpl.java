package org.shanyong.shop_java.agent.service.impl;

import org.shanyong.shop_java.agent.dto.AgentRefundCategoryStatsDTO;
import org.shanyong.shop_java.agent.dto.AgentRefundCategoryStatsResponse;
import org.shanyong.shop_java.agent.dto.AgentRefundProductStatsDTO;
import org.shanyong.shop_java.agent.dto.AgentRefundProductStatsResponse;
import org.shanyong.shop_java.agent.repository.AgentAfterSaleRepository;
import org.shanyong.shop_java.agent.service.AgentAfterSaleService;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;

@Service
public class AgentAfterSaleServiceImpl implements AgentAfterSaleService {

    private final AgentAfterSaleRepository agentAfterSaleRepository;

    public AgentAfterSaleServiceImpl(AgentAfterSaleRepository agentAfterSaleRepository) {
        this.agentAfterSaleRepository = agentAfterSaleRepository;
    }

    @Override
    @Transactional(readOnly = true)
    public AgentRefundProductStatsResponse getRecentProductRefundRates(Integer days, Integer limit) {
        DateRange dateRange = resolveRecentDateRange(days);
        List<AgentRefundProductStatsDTO> records = agentAfterSaleRepository.selectProductRefundRates(
            dateRange.startTime(),
            dateRange.endTime(),
            limit
        );

        AgentRefundProductStatsResponse response = new AgentRefundProductStatsResponse();
        response.setDays(dateRange.days());
        response.setStartDate(dateRange.startDate());
        response.setEndDate(dateRange.endDate());
        response.setRecords(records);
        response.setHasRefunds(records != null && !records.isEmpty());
        return response;
    }

    @Override
    @Transactional(readOnly = true)
    public AgentRefundCategoryStatsResponse getRecentCategoryRefundRates(Integer days, Integer limit) {
        DateRange dateRange = resolveRecentDateRange(days);
        List<AgentRefundCategoryStatsDTO> records = agentAfterSaleRepository.selectCategoryRefundRates(
            dateRange.startTime(),
            dateRange.endTime(),
            limit
        );

        AgentRefundCategoryStatsResponse response = new AgentRefundCategoryStatsResponse();
        response.setDays(dateRange.days());
        response.setStartDate(dateRange.startDate());
        response.setEndDate(dateRange.endDate());
        response.setRecords(records);
        response.setHasRefunds(records != null && !records.isEmpty());
        return response;
    }

    private DateRange resolveRecentDateRange(Integer days) {
        int normalizedDays = days == null ? 30 : days;
        LocalDate endDate = LocalDate.now();
        LocalDate startDate = endDate.minusDays(normalizedDays - 1L);
        LocalDateTime startTime = startDate.atStartOfDay();
        LocalDateTime endTime = endDate.plusDays(1).atStartOfDay();
        return new DateRange(normalizedDays, startDate, endDate, startTime, endTime);
    }

    private record DateRange(
        Integer days,
        LocalDate startDate,
        LocalDate endDate,
        LocalDateTime startTime,
        LocalDateTime endTime
    ) {
    }
}
