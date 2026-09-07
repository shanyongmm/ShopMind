package org.shanyong.shop_java.agent.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Python agent service request.
 */
public record AgentRequest(
    String message,
    @JsonProperty("max_retries") Integer maxRetries
) {
}

