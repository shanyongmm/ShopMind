# 架构说明

## 总体流程

1. 前端向 `POST /api/chat/stream` 发送用户问题。
2. FastAPI 将请求封装为 LangGraph 初始状态。
3. `plan_node` 提取核心问题并生成执行计划；相互独立、可同时查询的步骤 `depends_on` 留空。
4. `dispatcher_node` 按 `depends_on` 把计划拆成若干波次，波次内无依赖步骤经线程池并行派发给商品、订单、售后或直答 Agent。
5. 专职 Agent 通过 MCP Client 调用标准化工具，工具侧再访问 RAG 或 Java 业务接口；每个 Agent 输出前先对草稿做一次自评，必要时修正后给出最终步骤结果。
6. `synthesis_node` 汇总各步骤结果生成最终回答，并在节点内对最终草稿做有界自评修正（按 `max_retries` 控制轮数，替代原全局 `quality_check_node`/`rework_node`）。
7. 结果写入 PostgreSQL 会话表和 LangGraph checkpoint，供后续会话恢复。

## 模块职责

- `backend/app/core/`：配置、LLM、日志和持久化记忆基础设施
- `backend/app/api/`：HTTP 请求/响应 schema
- `backend/app/workflow/`：LangGraph 编排、Agent 工具、RAG 和状态模型
- `backend/app/data/`：本地知识库兜底数据
- `backend/app/mcp_service/`：MCP Server、`@mcp.tool()` 业务工具注册、MCP Client 与 LangChain 工具适配
- `backend/app/services/`：订单、商品、售后与线程存储服务
- `backend/app/main.py`：FastAPI 路由、SSE 输出和会话 API
- `frontend/`：原生静态聊天界面和会话列表

## 设计特点

- 多 Agent 拆分业务域，减少单模型一次性回答的不确定性
- 商品、订单和知识库检索能力通过 MCP 标准协议服务化，降低 Agent 与业务工具的耦合
- 计划步骤按 `depends_on` 依赖分波，波次内无依赖步骤并行执行，压缩单轮串行耗时
- 质量校验内置到每个业务 Agent 输出前与最终汇总节点内（自评 + 有界修正），省去独立的全局返工节点，缩短整图往返
- RAG 仅在需要知识依据时调用，避免无意义检索
- SSE 逐步输出节点和 token，前端更容易做“正在思考”的交互反馈
- 会话信息落库后可直接按 thread_id 恢复历史对话

## 目前约束

- 项目依赖外部 Milvus 向量服务；Java 业务服务源码在 `shop_java/`，已容器化并纳入 docker-compose
- 商品/订单等业务数据由 compose 内 `mysql`（`shop_db`）提供
- 售后创建工单接口目前以结构化占位信息返回，便于展示完整链路
