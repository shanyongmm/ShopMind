package org.shanyong.shop_java.agent.repository;


import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import org.shanyong.shop_java.agent.dto.AgentRecentOrderStatsDTO;

import java.time.LocalDateTime;

@Mapper
public interface AgentOrderStatsRepository {

    @Select({
        "SELECT",
        "created_stats.orderCount AS orderCount,",
        "created_stats.totalOrderAmount AS totalOrderAmount,",
        "paid_stats.paidOrderCount AS paidOrderCount,",
        "paid_stats.transactionAmount AS transactionAmount,",
        "CASE WHEN paid_stats.paidOrderCount = 0 THEN 0",
        "ELSE ROUND(paid_stats.transactionAmount / paid_stats.paidOrderCount, 2)",
        "END AS averageTransactionAmount",
        "FROM (",
        "  SELECT COUNT(*) AS orderCount, COALESCE(SUM(total_amount), 0) AS totalOrderAmount",
        "  FROM orders",
        "  WHERE created_at >= #{startTime} AND created_at < #{endTime}",
        ") created_stats",
        "CROSS JOIN (",
        "  SELECT COUNT(*) AS paidOrderCount, COALESCE(SUM(total_amount), 0) AS transactionAmount",
        "  FROM orders",
        "  WHERE status IN (1, 2, 3)",
        "  AND pay_time IS NOT NULL",
        "  AND pay_time >= #{startTime} AND pay_time < #{endTime}",
        ") paid_stats"
    })
    AgentRecentOrderStatsDTO selectRecentOrderStats(
        @Param("startTime") LocalDateTime startTime,
        @Param("endTime") LocalDateTime endTime
    );
}
