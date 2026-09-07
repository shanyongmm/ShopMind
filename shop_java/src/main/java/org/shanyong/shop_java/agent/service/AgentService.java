package org.shanyong.shop_java.agent.service;

import org.shanyong.shop_java.agent.dto.AgentChatRequest;
import org.shanyong.shop_java.agent.dto.AgentChatResponse;

/**
 * Agent chat service.
 */
public interface AgentService {

    AgentChatResponse chat(AgentChatRequest request);
}
