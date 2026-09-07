package org.shanyong.shop_java.agent.dto;

import lombok.Data;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

/**
 * Frontend chat request.
 */
@Data
public class AgentChatRequest {

    @NotBlank(message = "validation failed")
    @Size(max = 1000, message = "validation failed")
    private String message;

    @Min(value = 0, message = "validation failed")
    @Max(value = 5, message = "validation failed")
    private Integer maxRetries;
}
