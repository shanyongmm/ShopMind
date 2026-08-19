from datetime import datetime
from typing import Any

import psycopg
from psycopg.rows import dict_row

from ..config import get_settings


def _connect():
    return psycopg.connect(get_settings().postgres_uri, row_factory=dict_row)


def setup_thread_store() -> None:
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


def _make_title(message: str) -> str:
    title = " ".join(message.strip().split())
    if not title:
        return "新会话"
    return title[:30]


def upsert_thread(thread_id: str, user_message: str, assistant_answer: str) -> dict[str, Any]:
    title = _make_title(user_message)
    last_message = assistant_answer.strip() or user_message.strip()
    now = datetime.now().astimezone()

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
    with _connect() as conn:
        result = conn.execute("DELETE FROM chat_threads WHERE thread_id = %s", (thread_id,))
        return result.rowcount > 0
