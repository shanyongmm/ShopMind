package org.shanyong.shop_java.agent.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import org.shanyong.shop_java.agent.entity.Product;
import org.shanyong.shop_java.agent.repository.AgentProductRepository;
import org.shanyong.shop_java.agent.service.AgentProductService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;

@Service
public class AgentProductServiceImpl implements AgentProductService {

    @Autowired
    private AgentProductRepository agentProductRepository;

    @Override
    public Product getProductById(int id) {
        return agentProductRepository.selectById(id);
    }

    @Override
    public List<Product> getAllProductOrderBySalesCount() {
        QueryWrapper<Product> queryWrapper = new QueryWrapper<>();
        queryWrapper.orderByDesc("sales_count");
        return agentProductRepository.selectList(queryWrapper);
    }

    @Override
    public List<Product> getHotProducts(Integer limit) {
        QueryWrapper<Product> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("status", 1)
            .orderByDesc("sales_count", "created_at")
            .last("LIMIT " + normalizeLimit(limit));
        return agentProductRepository.selectList(queryWrapper);
    }

    @Override
    public List<Product> getRecommendedProducts(String keyword, Integer limit) {
        return agentProductRepository.selectRecommendedProductsByKeywords(
            resolveKeywords(keyword),
            normalizeLimit(limit)
        );
    }

    private int normalizeLimit(Integer limit) {
        return limit == null ? 10 : limit;
    }

    private List<String> resolveKeywords(String keyword) {
        Set<String> keywords = new LinkedHashSet<>();
        if (StringUtils.hasText(keyword)) {
            String normalizedKeyword = keyword.trim();
            keywords.add(normalizedKeyword);
            String lowerKeyword = normalizedKeyword.toLowerCase(Locale.ROOT);
            if (lowerKeyword.contains("phone") || lowerKeyword.contains("mobile")) {
                keywords.add("phone");
                keywords.add("mobile");
                keywords.add("smartphone");
                keywords.add("iphone");
                keywords.add("xiaomi");
            }
        }
        return new ArrayList<>(keywords);
    }
}
