package org.shanyong.shop_java.agent.controller;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.shanyong.shop_java.agent.dto.AgentChatRequest;
import org.shanyong.shop_java.agent.dto.AgentChatResponse;
import org.shanyong.shop_java.agent.service.AgentService;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import jakarta.validation.Valid;

@Slf4j
@Validated
@RestController
@RequestMapping("/api/agent")
@Tag(name = "Agent", description = "Python agent chat APIs")
public class AgentController {

    private final AgentService agentService;

    public AgentController(AgentService agentService) {
        this.agentService = agentService;
    }

    @PostMapping("/chat")
    @Operation(summary = "Agent chat", description = "Chat with Python agent service")
    public ResponseEntity<AgentChatResponse> chat(@Valid @RequestBody AgentChatRequest request) {
        log.info("Agent chat API request");
        return ResponseEntity.ok(agentService.chat(request));
    }
}
