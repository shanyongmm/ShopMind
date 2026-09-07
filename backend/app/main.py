import json
import logging

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .api.schemas import ChatMessage, ChatRequest, ChatResponse, ThreadDetail, ThreadSummary
from .core.cache import close_redis_cache, get_redis_health
from .core.config import get_settings
from .core.logging_config import configure_logging
from .core.memory import close_postgres_checkpointer
from .mcp_service.client import list_mcp_call_logs
from .workflow.graph import _graph_config, ask_agent, graph, stream_agent_events
from .services.thread_store import delete_thread, get_thread, list_threads, setup_thread_store, upsert_thread


configure_logging()
settings = get_settings()
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    setup_thread_store()


@app.on_event("shutdown")
def shutdown() -> None:
    close_postgres_checkpointer()
    close_redis_cache()


@app.get("/", include_in_schema=False)
def root() -> dict:
    return {
        "status": "running",
        "app": settings.app_name,
        "health": "/health",
        "docs": "/docs",
    }


def _serialize_sources(sources: list) -> list[dict]:
    serialized = []
    for source in sources or []:
        if hasattr(source, "model_dump"):
            serialized.append(source.model_dump())
        elif isinstance(source, dict):
            if "source_type" not in source:
                serialized.append(
                    {
                        "source_type": "unknown",
                        "source_name": source.get("source_name"),
                        "source_content": source.get("source_content") or str(source),
                        "relevance_score": source.get("relevance_score"),
                        "timestamp": source.get("timestamp"),
                    }
                )
            else:
                serialized.append(source)
        else:
            serialized.append(
                {
                    "source_type": "unknown",
                    "source_name": None,
                    "source_content": str(source),
                    "relevance_score": None,
                    "timestamp": None,
                }
            )
    return serialized


def _serialize_threads(threads: list[dict]) -> list[ThreadSummary]:
    return [
        ThreadSummary(
            thread_id=thread["thread_id"],
            title=thread["title"],
            last_message=thread["last_message"],
            created_at=thread["created_at"].isoformat(),
            updated_at=thread["updated_at"].isoformat(),
        )
        for thread in threads
    ]


def _serialize_messages(messages: list) -> list[ChatMessage]:
    serialized = []
    for message in messages or []:
        if isinstance(message, dict):
            role = message.get("role")
            content = str(message.get("content") or "").strip()
            if role in {"user", "assistant"} and content:
                serialized.append(ChatMessage(role=role, content=content))
            continue

        message_type = getattr(message, "type", "")
        content = str(getattr(message, "content", "") or "").strip()
        if not content:
            continue
        if message_type == "human":
            serialized.append(ChatMessage(role="user", content=content))
        elif message_type == "ai":
            serialized.append(ChatMessage(role="assistant", content=content))
    return serialized


@app.get("/health")
def health() -> dict:
    logger.info("health check")
    return {"status": "ok", "app": settings.app_name, "redis": get_redis_health()}


@app.get("/api/redis/health")
def redis_health() -> dict:
    return get_redis_health()


@app.get("/api/mcp/call-logs")
def mcp_call_logs(limit: int = Query(default=50, ge=1, le=200)) -> dict:
    return {"items": list_mcp_call_logs(limit), "limit": limit}


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    logger.info("chat request message_length=%s", len(request.message))
    try:
        result = ask_agent(request.message, request.max_retries, request.thread_id)
    except Exception as exc:
        logger.exception("chat failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    logger.info("chat response completed_steps=%s", len(result.get("step_results", {})))
    upsert_thread(request.thread_id, request.message, result.get("answer", ""))
    return ChatResponse(
        answer=result.get("answer", ""),
        thread_id=request.thread_id,
        plan_steps=result.get("plan_steps", []),
        sources=_serialize_sources(result.get("sources", [])),
        retry_count=result.get("retry_count", 0),
        quality_feedback=result.get("quality_feedback"),
        revision_suggestion=result.get("revision_suggestion"),
    )


@app.post("/api/chat/stream")
def chat_stream(request: ChatRequest) -> StreamingResponse:
    logger.info("chat_stream request message_length=%s", len(request.message))
    return StreamingResponse(
        _stream_with_thread_update(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


def _stream_with_thread_update(request: ChatRequest):
    for chunk in stream_agent_events(request.message, request.max_retries, request.thread_id):
        if chunk.startswith("event: done"):
            data_line = next((line for line in chunk.splitlines() if line.startswith("data:")), "")
            if data_line:
                try:
                    payload = json.loads(data_line.removeprefix("data:").strip())
                    upsert_thread(request.thread_id, request.message, payload.get("answer", ""))
                except json.JSONDecodeError:
                    logger.warning("failed to parse stream done payload")
        yield chunk


@app.get("/api/threads", response_model=list[ThreadSummary])
def threads() -> list[ThreadSummary]:
    setup_thread_store()
    return _serialize_threads(list_threads())


@app.get("/api/threads/{thread_id}", response_model=ThreadDetail)
def thread_detail(thread_id: str) -> ThreadDetail:
    thread = get_thread(thread_id)
    values = {}
    try:
        snapshot = graph.get_state(_graph_config(thread_id))
        values = snapshot.values or {}
    except Exception:
        logger.info("graph checkpoint state unavailable for thread_id=%s", thread_id)

    raw_messages = values.get("messages", []) or (thread.get("messages", []) if thread else [])
    messages = _serialize_messages(raw_messages)
    if not thread and not messages:
        raise HTTPException(status_code=404, detail="会话不存在")

    return ThreadDetail(
        thread_id=thread_id,
        title=thread["title"] if thread else None,
        messages=messages,
    )


@app.delete("/api/threads/{thread_id}")
def remove_thread(thread_id: str) -> dict:
    deleted = delete_thread(thread_id)
    checkpointer = getattr(graph, "checkpointer", None)
    if checkpointer is not None:
        try:
            checkpointer.delete_thread(thread_id)
        except Exception:
            logger.exception("failed to delete graph checkpoint thread_id=%s", thread_id)
    return {"deleted": deleted, "thread_id": thread_id}
