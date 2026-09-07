package org.shanyong.shop_java.agent.repository;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import org.shanyong.shop_java.agent.entity.Product;

import java.util.List;

@Mapper
public interface AgentProductRepository extends BaseMapper<Product> {

    @Select({
        "<script>",
        "SELECT p.*",
        "FROM products p",
        "LEFT JOIN categories c ON c.id = p.category_id",
        "LEFT JOIN categories pc ON pc.id = c.parent_id",
        "WHERE p.status = 1",
        "AND p.recommended = 1",
        "<if test='keywords != null and keywords.size() > 0'>",
        "AND (",
        "<foreach collection='keywords' item='keyword' separator=' OR '>",
        "(",
        "LOWER(p.name) LIKE CONCAT('%', LOWER(#{keyword}), '%')",
        "OR LOWER(p.sku) LIKE CONCAT('%', LOWER(#{keyword}), '%')",
        "OR LOWER(p.description) LIKE CONCAT('%', LOWER(#{keyword}), '%')",
        "OR LOWER(c.name) LIKE CONCAT('%', LOWER(#{keyword}), '%')",
        "OR LOWER(pc.name) LIKE CONCAT('%', LOWER(#{keyword}), '%')",
        ")",
        "</foreach>",
        ")",
        "</if>",
        "ORDER BY p.sales_count DESC, p.created_at DESC, p.id ASC",
        "LIMIT #{limit}",
        "</script>"
    })
    List<Product> selectRecommendedProductsByKeywords(
        @Param("keywords") List<String> keywords,
        @Param("limit") Integer limit
    );
}

