package org.shanyong.shop_java.agent.dto;

import lombok.Data;

/**
 * Frontend chat response.
 */
@Data
public class AgentChatResponse {

    private String answer;

    private String route;

    private String routeReason;

    private Double routeConfidence;

    private Integer retryCount;

    private String qualityFeedback;
}

