package org.shanyong.shop_java.agent.repository;


import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import org.shanyong.shop_java.agent.dto.AgentRefundCategoryStatsDTO;
import org.shanyong.shop_java.agent.dto.AgentRefundProductStatsDTO;

import java.time.LocalDateTime;
import java.util.List;

@Mapper
public interface AgentAfterSaleRepository {

    @Select({
        "<script>",
        "SELECT",
        "refund.productId AS productId,",
        "refund.productName AS productName,",
        "p.sku AS sku,",
        "refund.categoryId AS categoryId,",
        "refund.categoryName AS categoryName,",
        "COALESCE(sales.soldQuantity, 0) AS soldQuantity,",
        "refund.refundQuantity AS refundQuantity,",
        "refund.refundRequestCount AS refundRequestCount,",
        "refund.refundAmount AS refundAmount,",
        "CASE WHEN COALESCE(sales.soldQuantity, 0) = 0 THEN 0",
        "ELSE ROUND(refund.refundQuantity * 1.0 / sales.soldQuantity, 4)",
        "END AS refundRate,",
        "refund.latestApplyTime AS latestApplyTime",
        "FROM (",
        "  SELECT",
        "  asi.product_id AS productId,",
        "  MAX(asi.product_name_snapshot) AS productName,",
        "  COALESCE(pc.id, c.id) AS categoryId,",
        "  COALESCE(pc.name, c.name) AS categoryName,",
        "  COALESCE(SUM(asi.quantity), 0) AS refundQuantity,",
        "  COUNT(DISTINCT r.id) AS refundRequestCount,",
        "  COALESCE(SUM(asi.refund_amount), 0) AS refundAmount,",
        "  MAX(r.apply_time) AS latestApplyTime",
        "  FROM after_sale_requests r",
        "  JOIN after_sale_items asi ON asi.after_sale_id = r.id",
        "  JOIN products refund_product ON refund_product.id = asi.product_id",
        "  JOIN categories c ON c.id = refund_product.category_id",
        "  LEFT JOIN categories pc ON pc.id = c.parent_id",
        "  WHERE r.type IN (0, 1)",
        "  AND r.status NOT IN (2, 7)",
        "  AND asi.refund_amount > 0",
        "  <if test='startTime != null'>AND r.apply_time &gt;= #{startTime}</if>",
        "  <if test='endTime != null'>AND r.apply_time &lt; #{endTime}</if>",
        "  GROUP BY asi.product_id, COALESCE(pc.id, c.id), COALESCE(pc.name, c.name)",
        ") refund",
        "JOIN products p ON p.id = refund.productId",
        "LEFT JOIN (",
        "  SELECT",
        "  oi.product_id AS productId,",
        "  COALESCE(SUM(oi.quantity), 0) AS soldQuantity",
        "  FROM order_items oi",
        "  JOIN orders o ON o.id = oi.order_id",
        "  WHERE o.status IN (1, 2, 3)",
        "  AND o.pay_time IS NOT NULL",
        "  <if test='startTime != null'>AND o.pay_time &gt;= #{startTime}</if>",
        "  <if test='endTime != null'>AND o.pay_time &lt; #{endTime}</if>",
        "  GROUP BY oi.product_id",
        ") sales ON sales.productId = refund.productId",
        "ORDER BY refundRate DESC, refund.refundAmount DESC, refund.refundQuantity DESC, refund.productId ASC",
        "LIMIT #{limit}",
        "</script>"
    })
    List<AgentRefundProductStatsDTO> selectProductRefundRates(
        @Param("startTime") LocalDateTime startTime,
        @Param("endTime") LocalDateTime endTime,
        @Param("limit") Integer limit
    );

    @Select({
        "<script>",
        "SELECT",
        "refund.categoryId AS categoryId,",
        "refund.categoryName AS categoryName,",
        "COALESCE(sales.soldQuantity, 0) AS soldQuantity,",
        "refund.refundQuantity AS refundQuantity,",
        "refund.refundRequestCount AS refundRequestCount,",
        "refund.refundAmount AS refundAmount,",
        "CASE WHEN COALESCE(sales.soldQuantity, 0) = 0 THEN 0",
        "ELSE ROUND(refund.refundQuantity * 1.0 / sales.soldQuantity, 4)",
        "END AS refundRate,",
        "refund.latestApplyTime AS latestApplyTime",
        "FROM (",
        "  SELECT",
        "  COALESCE(pc.id, c.id) AS categoryId,",
        "  COALESCE(pc.name, c.name) AS categoryName,",
        "  COALESCE(SUM(asi.quantity), 0) AS refundQuantity,",
        "  COUNT(DISTINCT r.id) AS refundRequestCount,",
        "  COALESCE(SUM(asi.refund_amount), 0) AS refundAmount,",
        "  MAX(r.apply_time) AS latestApplyTime",
        "  FROM after_sale_requests r",
        "  JOIN after_sale_items asi ON asi.after_sale_id = r.id",
        "  JOIN products refund_product ON refund_product.id = asi.product_id",
        "  JOIN categories c ON c.id = refund_product.category_id",
        "  LEFT JOIN categories pc ON pc.id = c.parent_id",
        "  WHERE r.type IN (0, 1)",
        "  AND r.status NOT IN (2, 7)",
        "  AND asi.refund_amount > 0",
        "  <if test='startTime != null'>AND r.apply_time &gt;= #{startTime}</if>",
        "  <if test='endTime != null'>AND r.apply_time &lt; #{endTime}</if>",
        "  GROUP BY COALESCE(pc.id, c.id), COALESCE(pc.name, c.name)",
        ") refund",
        "LEFT JOIN (",
        "  SELECT",
        "  COALESCE(pc.id, c.id) AS categoryId,",
        "  COALESCE(pc.name, c.name) AS categoryName,",
        "  COALESCE(SUM(oi.quantity), 0) AS soldQuantity",
        "  FROM order_items oi",
        "  JOIN orders o ON o.id = oi.order_id",
        "  JOIN products sold_product ON sold_product.id = oi.product_id",
        "  JOIN categories c ON c.id = sold_product.category_id",
        "  LEFT JOIN categories pc ON pc.id = c.parent_id",
        "  WHERE o.status IN (1, 2, 3)",
        "  AND o.pay_time IS NOT NULL",
        "  <if test='startTime != null'>AND o.pay_time &gt;= #{startTime}</if>",
        "  <if test='endTime != null'>AND o.pay_time &lt; #{endTime}</if>",
        "  GROUP BY COALESCE(pc.id, c.id), COALESCE(pc.name, c.name)",
        ") sales ON sales.categoryId = refund.categoryId",
        "ORDER BY refundRate DESC, refund.refundAmount DESC, refund.refundQuantity DESC, refund.categoryId ASC",
        "LIMIT #{limit}",
        "</script>"
    })
    List<AgentRefundCategoryStatsDTO> selectCategoryRefundRates(
        @Param("startTime") LocalDateTime startTime,
        @Param("endTime") LocalDateTime endTime,
        @Param("limit") Integer limit
    );
}
