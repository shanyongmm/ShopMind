package org.shanyong.shop_java.agent.service.impl;

import lombok.extern.slf4j.Slf4j;
import org.shanyong.shop_java.agent.config.AgentProperties;
import org.shanyong.shop_java.agent.dto.AgentChatRequest;
import org.shanyong.shop_java.agent.dto.AgentChatResponse;
import org.shanyong.shop_java.agent.dto.AgentRequest;
import org.shanyong.shop_java.agent.dto.AgentResponse;
import org.shanyong.shop_java.agent.service.AgentService;
import org.shanyong.shop_java.common.exception.CustomException;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientResponseException;

import java.time.Duration;

@Slf4j
@Service
public class AgentServiceImpl implements AgentService {

    private final AgentProperties properties;
    private final WebClient webClient;

    public AgentServiceImpl(AgentProperties properties, WebClient.Builder webClientBuilder) {
        this.properties = properties;
        this.webClient = webClientBuilder
            .baseUrl(properties.getBaseUrl())
            .build();
    }

    @Override
    public AgentChatResponse chat(AgentChatRequest request) {
        final String message = request.getMessage().trim();
        final Integer maxRetries = request.getMaxRetries() == null
            ? properties.getMaxRetries()
            : request.getMaxRetries();

        log.info("Agent chat request, messageLength: {}, maxRetries: {}", message.length(), maxRetries);

        final AgentResponse response = callPythonAgent(new AgentRequest(message, maxRetries));
        return convertToChatResponse(response);
    }

    private AgentResponse callPythonAgent(AgentRequest request) {
        try {
            return webClient.post()
                .uri(properties.getChatPath())
                .bodyValue(request)
                .retrieve()
                .bodyToMono(AgentResponse.class)
                .block(Duration.ofMillis(properties.getTimeoutMillis()));
        } catch (WebClientResponseException e) {
            log.warn(
                "Python agent service returned error, status: {}, body: {}",
                e.getStatusCode().value(),
                e.getResponseBodyAsString()
            );
            throw new CustomException("AGENT_SERVICE_ERROR", "Agent service returned an error");
        } catch (Exception e) {
            log.warn("Python agent service request failed", e);
            throw new CustomException(
                "AGENT_SERVICE_UNAVAILABLE",
                "Agent service unavailable, please try again later"
            );
        }
    }

    private AgentChatResponse convertToChatResponse(AgentResponse response) {
        if (response == null) {
            throw new CustomException("AGENT_EMPTY_RESPONSE", "Agent service returned empty response");
        }

        AgentChatResponse chatResponse = new AgentChatResponse();
        chatResponse.setAnswer(response.answer());
        chatResponse.setRoute(response.route());
        chatResponse.setRouteReason(response.routeReason());
        chatResponse.setRouteConfidence(response.routeConfidence());
        chatResponse.setRetryCount(response.retryCount());
        chatResponse.setQualityFeedback(response.qualityFeedback());
        return chatResponse;
    }
}
