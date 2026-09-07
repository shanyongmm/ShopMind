# Docker 基础服务部署

本项目通过 Docker Compose 部署基础服务，后端和前端在项目中本地运行：

- `mysql`：业务数据库 `shop_db`（首次启动自动导入 `deploy/mysql/init/01-shop_db.sql`）
- `java`：Java 业务服务（源码在 `shop_java/`，提供 `/api/agent/*` 接口）
- `postgres`：LangGraph checkpoint 与会话列表存储
- `redis`：MCP 只读业务查询缓存
- `etcd`：Milvus 元数据依赖
- `minio`：Milvus 对象存储依赖
- `milvus`：RAG 向量数据库
- `mcp`：独立部署的 ShopMind MCP 工具服务

## 启动

1. 准备环境变量

```powershell
Copy-Item .env.example .env
```

2. 编辑 `.env`，至少填写：

```text
LLM_BASE_URL=
LLM_API_KEY=
LLM_MODEL=
DASHSCOPE_API_KEY=
EMBED_MODEL_NAME=
```

3. 启动基础服务

```powershell
docker compose up -d --build
```

4. 访问服务

- MCP 服务：`http://127.0.0.1:8010/mcp`
- Milvus：`http://127.0.0.1:19530`
- Redis：`127.0.0.1:6379`
- PostgreSQL：`127.0.0.1:5432`
- Redis 健康检查：`http://127.0.0.1:8000/api/redis/health`
- MCP 调用记录：`http://127.0.0.1:8000/api/mcp/call-logs?limit=50`

## 本地程序配置

后端本地运行时，`.env` 使用宿主机地址：

```text
MILVUS_URL=http://127.0.0.1:19530
SHOPMIND_MCP_URL=http://127.0.0.1:8010/mcp
REDIS_URL=redis://127.0.0.1:6379/0
REDIS_MCP_CALL_LOG_ENABLED=true
POSTGRES_URI=postgresql://customer_agent:customer_agent_pwd@127.0.0.1:5432/customer_agent_memory?sslmode=disable
MEMORY_MODE=auto
```

`MEMORY_MODE=auto` 会在 PostgreSQL 可用时启用 LangGraph checkpoint 和会话列表持久化；如果希望数据库不可用时直接报错，可改为 `MEMORY_MODE=postgres`。

MCP 容器内部会自动使用 Docker 服务名访问 Milvus、Redis 和 PostgreSQL。

## 启动本地程序

后端：

```powershell
cd backend
pip install -r requirements.txt
python run.py
```

前端：

```powershell
cd frontend
python -m http.server 5500
```

## Java 业务服务说明

Java 业务服务源码位于 `shop_java/`，已加入 docker-compose（`java` 服务，端口映射 `8080:8080`），构建见 `shop_java/Dockerfile`（Maven 多阶段 + Temurin 17）。它连接 compose 内 `mysql:3306/shop_db`，通过 `MYSQL_USER` / `MYSQL_PASSWORD`（默认 `shopmind` / `shopmind_pwd`）访问。

`mcp` 容器在 compose 网络内通过服务名访问 Java：

```text
JAVA_API_BASE_URL=http://java:8080
```

因此不再依赖 `host.docker.internal`。宿主机本地直跑后端/MCP 时，`JAVA_API_BASE_URL` 使用 `http://127.0.0.1:8080` 即可（见 `.env`）。

查看 Java 运行日志：

```bash
docker compose logs -f java
```

## 常用命令

```bash
docker compose ps
docker compose logs -f mcp
docker compose logs -f redis
docker compose logs -f milvus
docker compose down
docker compose down -v
```

`docker compose down -v` 会删除数据库和向量库数据卷，只在需要清空演示数据时使用。
