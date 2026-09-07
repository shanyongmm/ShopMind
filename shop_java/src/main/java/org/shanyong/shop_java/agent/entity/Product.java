package org.shanyong.shop_java.agent.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.experimental.Accessors;

import java.time.LocalDateTime;

@Data
@EqualsAndHashCode(callSuper = false)
@Accessors(chain = true)
@TableName("products")
public class Product {

    @TableId(type = IdType.AUTO)
    private Long id;

    private Long categoryId;

    private String name;

    private String sku;

    private String description;

    private Double price;

    private Integer stock;

    private String imageUrl;

    private Integer status;

    private Integer recommended;

    private Integer salesCount;

    private LocalDateTime createdAt;

    private LocalDateTime updatedAt;
}

