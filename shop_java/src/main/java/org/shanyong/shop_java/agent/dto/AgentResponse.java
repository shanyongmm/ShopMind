package org.shanyong.shop_java.agent.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Python agent service response.
 */
public record AgentResponse(
    String answer,
    String route,
    @JsonProperty("route_reason") String routeReason,
    @JsonProperty("route_confidence") Double routeConfidence,
    @JsonProperty("retry_count") Integer retryCount,
    @JsonProperty("quality_feedback") String qualityFeedback
) {
}

