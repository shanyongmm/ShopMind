package org.shanyong.shop_java.agent.service;

import org.shanyong.shop_java.agent.entity.Product;

import java.util.List;

public interface AgentProductService {
    List<Product>getAllProductOrderBySalesCount();
    Product getProductById(int id);
    List<Product> getHotProducts(Integer limit);
    List<Product> getRecommendedProducts(String keyword, Integer limit);
}
