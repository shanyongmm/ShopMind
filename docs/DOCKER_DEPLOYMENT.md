# Docker 一键部署

本项目支持通过 Docker Compose 启动完整演示环境：

- `postgres`：LangGraph checkpoint 与会话列表存储
- `etcd`：Milvus 元数据依赖
- `minio`：Milvus 对象存储依赖
- `milvus`：RAG 向量数据库
- `backend`：FastAPI + LangGraph Agent 服务
- `frontend`：Nginx 托管静态聊天页面

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

3. 一键启动

```bash
docker compose up -d --build
```

4. 访问服务

- 前端页面：`http://127.0.0.1:5500`
- 后端接口：`http://127.0.0.1:8000`
- FastAPI 文档：`http://127.0.0.1:8000/docs`
- Milvus：`http://127.0.0.1:19530`

## Java 业务服务说明

当前仓库不包含 Java 业务服务源码，因此 Compose 默认将：

```text
JAVA_API_BASE_URL=http://host.docker.internal:8080
```

用于访问宿主机上运行的 Java 服务。如果后续把 Java 服务也放进本仓库，可以在 `docker-compose.yml` 中新增 `java-api` 服务，并把该变量改为：

```text
JAVA_API_BASE_URL=http://java-api:8080
```

## 常用命令

```bash
docker compose ps
docker compose logs -f backend
docker compose logs -f milvus
docker compose down
docker compose down -v
```

`docker compose down -v` 会删除数据库和向量库数据卷，只在需要清空演示数据时使用。

