# 架构说明

## 总体流程

1. 前端向 `POST /api/chat/stream` 发送用户问题。
2. FastAPI 将请求封装为 LangGraph 初始状态。
3. `plan_node` 提取核心问题并生成执行计划。
4. `dispatcher_node` 根据计划把任务路由到商品、订单、售后或直答 Agent。
5. 专职 Agent 在工具层调用 RAG 或 Java 业务接口。
6. `synthesis_node` 汇总各步骤结果生成最终回答。
7. `quality_check_node` 对答案做质量评估，必要时进入 `rework_node` 重写。
8. 结果写入 PostgreSQL 会话表和 LangGraph checkpoint，供后续会话恢复。

## 模块职责

- `backend/app/graph.py`：核心工作流编排、节点定义、质量回路和记忆压缩
- `backend/app/tools.py`：大模型工具、RAG 工具和 Java 业务接口工具封装
- `backend/app/rag.py`：Milvus 向量检索与知识片段格式化
- `backend/app/services/`：订单、商品、售后与线程存储服务
- `backend/app/main.py`：FastAPI 路由、SSE 输出和会话 API
- `frontend/`：原生静态聊天界面和会话列表

## 设计特点

- 多 Agent 拆分业务域，减少单模型一次性回答的不确定性
- RAG 仅在需要知识依据时调用，避免无意义检索
- SSE 逐步输出节点和 token，前端更容易做“正在思考”的交互反馈
- 会话信息落库后可直接按 thread_id 恢复历史对话

## 目前约束

- 项目依赖外部 Milvus 和 Java 业务服务，仓库内不包含这些服务的实现
- 售后创建工单接口目前以结构化占位信息返回，便于展示完整链路

