package org.shanyong.shop_java.agent.repository;


import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import org.shanyong.shop_java.agent.dto.AgentDailySalesDTO;
import org.shanyong.shop_java.agent.dto.AgentProductSalesDTO;
import org.shanyong.shop_java.agent.dto.AgentSalesOrderDTO;
import org.shanyong.shop_java.agent.dto.AgentSalesSummaryDTO;

import java.time.LocalDateTime;
import java.util.List;

@Mapper
public interface AgentSalesRepository {

    @Select({
        "<script>",
        "SELECT",
        "COUNT(*) AS orderCount,",
        "COALESCE(SUM(o.total_amount), 0) AS totalAmount,",
        "COALESCE(SUM(item_stats.total_quantity), 0) AS totalQuantity,",
        "COALESCE(ROUND(AVG(o.total_amount), 2), 0) AS averageOrderAmount",
        "FROM orders o",
        "LEFT JOIN (",
        "  SELECT order_id, SUM(quantity) AS total_quantity",
        "  FROM order_items",
        "  GROUP BY order_id",
        ") item_stats ON item_stats.order_id = o.id",
        "WHERE o.status IN (1, 2, 3)",
        "AND o.pay_time IS NOT NULL",
        "<if test='startTime != null'>AND o.pay_time &gt;= #{startTime}</if>",
        "<if test='endTime != null'>AND o.pay_time &lt; #{endTime}</if>",
        "</script>"
    })
    AgentSalesSummaryDTO selectSalesSummary(
        @Param("startTime") LocalDateTime startTime,
        @Param("endTime") LocalDateTime endTime
    );

    @Select({
        "<script>",
        "SELECT",
        "DATE_FORMAT(o.pay_time, '%Y-%m-%d') AS saleDate,",
        "COUNT(*) AS orderCount,",
        "COALESCE(SUM(item_stats.total_quantity), 0) AS salesQuantity,",
        "COALESCE(SUM(o.total_amount), 0) AS salesAmount",
        "FROM orders o",
        "LEFT JOIN (",
        "  SELECT order_id, SUM(quantity) AS total_quantity",
        "  FROM order_items",
        "  GROUP BY order_id",
        ") item_stats ON item_stats.order_id = o.id",
        "WHERE o.status IN (1, 2, 3)",
        "AND o.pay_time IS NOT NULL",
        "<if test='startTime != null'>AND o.pay_time &gt;= #{startTime}</if>",
        "<if test='endTime != null'>AND o.pay_time &lt; #{endTime}</if>",
        "GROUP BY DATE_FORMAT(o.pay_time, '%Y-%m-%d')",
        "ORDER BY saleDate ASC",
        "</script>"
    })
    List<AgentDailySalesDTO> selectDailySales(
        @Param("startTime") LocalDateTime startTime,
        @Param("endTime") LocalDateTime endTime
    );

    @Select({
        "<script>",
        "SELECT",
        "p.id AS productId,",
        "p.name AS productName,",
        "p.sku AS sku,",
        "COALESCE(SUM(oi.quantity), 0) AS salesQuantity,",
        "COALESCE(SUM(oi.amount), 0) AS salesAmount,",
        "COUNT(DISTINCT o.id) AS orderCount",
        "FROM order_items oi",
        "JOIN orders o ON o.id = oi.order_id",
        "JOIN products p ON p.id = oi.product_id",
        "WHERE o.status IN (1, 2, 3)",
        "AND o.pay_time IS NOT NULL",
        "<if test='startTime != null'>AND o.pay_time &gt;= #{startTime}</if>",
        "<if test='endTime != null'>AND o.pay_time &lt; #{endTime}</if>",
        "GROUP BY p.id, p.name, p.sku",
        "ORDER BY salesQuantity DESC, salesAmount DESC, productId ASC",
        "LIMIT #{limit}",
        "</script>"
    })
    List<AgentProductSalesDTO> selectTopProducts(
        @Param("startTime") LocalDateTime startTime,
        @Param("endTime") LocalDateTime endTime,
        @Param("limit") Integer limit
    );

    @Select({
        "SELECT",
        "o.id AS orderId,",
        "o.order_no AS orderNo,",
        "o.user_id AS userId,",
        "o.status AS status,",
        "o.total_amount AS totalAmount,",
        "COALESCE(item_stats.total_quantity, 0) AS totalQuantity,",
        "o.created_at AS createdAt,",
        "o.pay_time AS payTime",
        "FROM orders o",
        "LEFT JOIN (",
        "  SELECT order_id, SUM(quantity) AS total_quantity",
        "  FROM order_items",
        "  GROUP BY order_id",
        ") item_stats ON item_stats.order_id = o.id",
        "WHERE o.status IN (1, 2, 3)",
        "AND o.pay_time IS NOT NULL",
        "ORDER BY o.pay_time DESC, o.id DESC",
        "LIMIT #{limit}"
    })
    List<AgentSalesOrderDTO> selectRecentPaidOrders(@Param("limit") Integer limit);
}
