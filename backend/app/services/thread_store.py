from datetime import datetime
import logging
from typing import Any

import psycopg
from psycopg.rows import dict_row

from ..core.config import get_settings
from ..core.memory import is_persistent_memory_disabled, is_persistent_memory_required


_DEMO_THREADS: dict[str, dict[str, Any]] = {}
_THREAD_STORE_BACKEND: str | None = None
logger = logging.getLogger(__name__)


def _is_demo_mode() -> bool:
    global _THREAD_STORE_BACKEND
    if _THREAD_STORE_BACKEND is None:
        setup_thread_store()
    return _THREAD_STORE_BACKEND != "postgres"


def _connect():
    return psycopg.connect(get_settings().postgres_uri, row_factory=dict_row)


def setup_thread_store() -> None:
    global _THREAD_STORE_BACKEND
    if is_persistent_memory_disabled():
        _THREAD_STORE_BACKEND = "memory"
        return

    try:
        with _connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_threads (
                    thread_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    last_message TEXT NOT NULL DEFAULT '',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
        _THREAD_STORE_BACKEND = "postgres"
        logger.info("thread store initialized with postgres")
    except Exception:
        if is_persistent_memory_required():
            logger.exception("postgres thread store initialization failed")
            raise
        _THREAD_STORE_BACKEND = "memory"
        logger.warning("postgres thread store unavailable, using in-memory thread list", exc_info=True)


def _make_title(message: str) -> str:
    title = " ".join(message.strip().split())
    if not title:
        return "新会话"
    return title[:30]


def upsert_thread(thread_id: str, user_message: str, assistant_answer: str) -> dict[str, Any]:
    title = _make_title(user_message)
    last_message = assistant_answer.strip() or user_message.strip()
    now = datetime.now().astimezone()

    if _is_demo_mode():
        existing = _DEMO_THREADS.get(thread_id)
        messages = list(existing.get("messages", [])) if existing else []
        messages.append({"role": "user", "content": user_message})
        if assistant_answer.strip():
            messages.append({"role": "assistant", "content": assistant_answer})

        row = {
            "thread_id": thread_id,
            "title": existing["title"] if existing else title,
            "last_message": last_message[:300],
            "created_at": existing["created_at"] if existing else now,
            "updated_at": now,
            "messages": messages,
        }
        _DEMO_THREADS[thread_id] = row
        return row

    with _connect() as conn:
        row = conn.execute(
            """
            INSERT INTO chat_threads (thread_id, title, last_message, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (thread_id) DO UPDATE
            SET last_message = EXCLUDED.last_message,
                updated_at = EXCLUDED.updated_at
            RETURNING thread_id, title, last_message, created_at, updated_at
            """,
            (thread_id, title, last_message[:300], now, now),
        ).fetchone()
        return dict(row)


def list_threads(limit: int = 100) -> list[dict[str, Any]]:
    if _is_demo_mode():
        return sorted(
            _DEMO_THREADS.values(),
            key=lambda row: row["updated_at"],
            reverse=True,
        )[:limit]

    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT thread_id, title, last_message, created_at, updated_at
            FROM chat_threads
            ORDER BY updated_at DESC
            LIMIT %s
            """,
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]


def get_thread(thread_id: str) -> dict[str, Any] | None:
    if _is_demo_mode():
        return _DEMO_THREADS.get(thread_id)

    with _connect() as conn:
        row = conn.execute(
            """
            SELECT thread_id, title, last_message, created_at, updated_at
            FROM chat_threads
            WHERE thread_id = %s
            """,
            (thread_id,),
        ).fetchone()
        return dict(row) if row else None


def delete_thread(thread_id: str) -> bool:
    if _is_demo_mode():
        return _DEMO_THREADS.pop(thread_id, None) is not None

    with _connect() as conn:
        result = conn.execute("DELETE FROM chat_threads WHERE thread_id = %s", (thread_id,))
        return result.rowcount > 0
