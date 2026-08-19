from functools import lru_cache

from langchain_openai import ChatOpenAI

from .config import get_settings


@lru_cache
def get_chat_model() -> ChatOpenAI:
    settings = get_settings()
    return ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
    )
