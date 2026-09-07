# ShopMind 智能电商交易与多 Agent 客服平台

一个面向电商客服场景的多 Agent 问答系统。后端基于 FastAPI + LangGraph 编排，接入 RAG、商品/订单/售后工具、PostgreSQL 会话记忆和 SSE 流式输出；前端使用原生 HTML/CSS/JS 实现多会话聊天界面，方便面试官直接拉取查看。

![架构图](./langgraph_agent_architecture.svg)

## 项目亮点

- 多阶段工作流：问题规划、任务分发、专职 Agent 执行、答案汇总、质量评估与回修
- 多业务域覆盖：商品咨询、订单查询、物流追踪、售后状态与政策查询
- MCP 工具服务：商品、订单和知识库检索能力通过独立 MCP Server 标准化暴露
- 检索增强：Milvus 向量检索接入知识库，支持基于上下文的回答生成
- 会话管理：PostgreSQL 持久化会话列表与 LangGraph checkpoint
- 流式体验：`/api/chat/stream` 基于 SSE 输出节点和 token 事件
- 面试友好：仓库结构清晰，README 可直接作为项目说明文档使用

## 技术栈

`FastAPI` `LangGraph` `LangChain` `MCP` `PostgreSQL` `Milvus` `DashScope` `Java API` `HTML/CSS/JS`

## 目录结构

```text
.
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── clients/
│   │   ├── core/
│   │   ├── data/
│   │   ├── mcp_service/
│   │   ├── services/
│   │   └── workflow/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── run.py
├── deploy/
│   └── nginx.conf
├── docs/
│   ├── ARCHITECTURE.md
│   └── DOCKER_DEPLOYMENT.md
├── frontend/
│   ├── Dockerfile
│   ├── index.html
│   ├── script.js
│   └── style.css
├── docker-compose.yml
├── .env.example
└── README.md
```

## 快速启动

Docker Compose 启动 MySQL、Java 业务服务、PostgreSQL、Redis、Milvus、etcd、MinIO 和 MCP 服务，后端与前端在项目中本地启动。Java 与 MySQL 已容器化（见 `shop_java/Dockerfile` 与 `docker-compose.yml`），`mysql` 服务首次启动会自动导入 `deploy/mysql/init/` 下的 `shop_db` 初始化数据，MCP 容器通过服务名 `http://java:8080` 访问 Java。

1. 复制环境变量模板并填写模型 Key

PowerShell:

```powershell
Copy-Item .env.example .env
```

2. 启动基础服务（首次会拉取并构建镜像）

```powershell
docker compose up -d --build
```

3. 启动后端

```powershell
cd backend
pip install -r requirements.txt
python run.py
```

4. 启动前端

```powershell
cd frontend
python -m http.server 5500
```

访问地址：

- 前端页面：`http://127.0.0.1:5500`
- 后端接口：`http://127.0.0.1:8000`
- 接口文档：`http://127.0.0.1:8000/docs`
- MCP 服务：`http://127.0.0.1:8010/mcp`

## API

- `GET /`
- `GET /health`
- `POST /api/chat`
- `POST /api/chat/stream`
- `GET /api/threads`
- `GET /api/threads/{thread_id}`
- `DELETE /api/threads/{thread_id}`
- `GET /api/redis/health`
- `GET /api/mcp/call-logs`

## 环境变量

| 变量 | 说明 |
| --- | --- |
| `LLM_MODEL` | 大模型名称 |
| `LLM_API_KEY` | 大模型 API Key |
| `LLM_BASE_URL` | 大模型服务地址 |
| `DASHSCOPE_API_KEY` | Embedding 服务 Key |
| `EMBED_MODEL_NAME` | 向量化模型名称 |
| `MILVUS_URL` | Milvus 地址 |
| `DB_NAME` | Milvus 数据库名 |
| `COL_NAME` | Milvus 集合名 |
| `JAVA_API_BASE_URL` | 业务 Java 服务地址 |
| `JAVA_API_TIMEOUT` | Java 服务超时 |
| `JAVA_API_TOKEN` | Java 服务鉴权 Token |
| `DATA_MODE` | 业务数据模式，默认 demo |
| `RAG_MODE` | 知识库模式，默认 local |
| `MEMORY_MODE` | 短期记忆模式，默认 auto；可设置 postgres 强制启用 |
| `SHOPMIND_MCP_URL` | 后端访问 MCP 服务的地址 |
| `SHOPMIND_MCP_TIMEOUT` | MCP Client 请求超时 |
| `SHOPMIND_MCP_SSE_READ_TIMEOUT` | MCP Streamable HTTP 读取超时 |
| `SHOPMIND_MCP_TRANSPORT` | MCP Server 传输模式，默认 streamable-http |
| `SHOPMIND_MCP_HOST` | MCP HTTP 服务监听地址 |
| `SHOPMIND_MCP_PORT` | MCP HTTP 服务端口 |
| `SHOPMIND_MCP_PATH` | MCP Streamable HTTP 路径 |
| `REDIS_URL` | Redis 连接串 |
| `REDIS_TIMEOUT` | Redis 连接和读写超时时间 |
| `REDIS_MCP_CALL_LOG_ENABLED` | 是否将 MCP 调用记录写入 Redis |
| `REDIS_MCP_CALL_LOG_KEY` | MCP 调用记录 Redis list key |
| `REDIS_MCP_CALL_LOG_LIMIT` | Redis 中保留的 MCP 调用记录数量 |
| `REDIS_MCP_CALL_LOG_TTL` | MCP 调用记录过期时间，单位秒 |
| `POSTGRES_URI` | PostgreSQL 连接串 |



## 说明

- `frontend/index.html` 可直接打开，或通过静态服务访问
- Docker Compose 部署 MySQL、Java、PostgreSQL、Redis、Milvus、etcd、MinIO 和 MCP 服务
- 后端和前端需要在项目中单独启动
- Java 业务服务源码位于 `shop_java/`，已容器化并加入 docker-compose（`java` 服务，端口 8080）；MCP 容器通过服务名 `http://java:8080` 访问，不再依赖 `host.docker.internal`
- MySQL 由 compose 内 `mysql` 服务提供（`shop_db`，首次启动自动导入 `deploy/mysql/init/01-shop_db.sql`），宿主机 3306 已有 MySQL 时可保留不动，容器端口映射为 3307 供排查
- 售后“创建工单”接口目前返回结构化占位信息，便于展示完整链路
- 后端已按 `core / api / workflow / data / services / clients / mcp_service` 分层，MCP 工具服务独立部署后由后端客户端调用

更多架构说明见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)。
MCP 服务说明见 [docs/MCP_SERVICE.md](docs/MCP_SERVICE.md)。
Docker 部署说明见 [docs/DOCKER_DEPLOYMENT.md](docs/DOCKER_DEPLOYMENT.md)。
