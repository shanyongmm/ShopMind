package org.shanyong.shop_java.agent.config;

import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

/**
 * Python agent service configuration.
 */
@Getter
@Setter
@Component
@ConfigurationProperties(prefix = "app.agent")
public class AgentProperties {

    private String baseUrl = "http://localhost:8000";

    private String chatPath = "/api/chat";

    private Integer maxRetries = 2;

    private Integer timeoutMillis = 30000;
}

