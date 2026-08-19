from contextlib import ExitStack
import logging

from langgraph.checkpoint.postgres import PostgresSaver

from .config import get_settings


logger = logging.getLogger(__name__)
_exit_stack = ExitStack()


def create_postgres_checkpointer() -> PostgresSaver:
    settings = get_settings()
    checkpointer = _exit_stack.enter_context(PostgresSaver.from_conn_string(settings.postgres_uri))
    checkpointer.setup()
    logger.info("postgres checkpointer initialized")
    return checkpointer


def close_postgres_checkpointer() -> None:
    _exit_stack.close()
