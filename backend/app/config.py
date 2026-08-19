from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_DIR / ".env"

load_dotenv(ENV_PATH, override=True)


class Settings(BaseSettings):
    llm_model: str = Field(alias="LLM_MODEL")
    llm_api_key: str = Field(alias="LLM_API_KEY")
    llm_base_url: str = Field(alias="LLM_BASE_URL")

    dashscope_api_key: str | None = Field(default=None, alias="DASHSCOPE_API_KEY")
    embed_model_name: str | None = Field(default=None, alias="EMBED_MODEL_NAME")

    milvus_url: str | None = Field(default=None, alias="MILVUS_URL")
    db_name: str | None = Field(default=None, alias="DB_NAME")
    collection: str | None = Field(default=None, alias="COL_NAME")

    java_api_base_url: str = Field(default="http://127.0.0.1:8080", alias="JAVA_API_BASE_URL")
    java_api_timeout: float = Field(default=10.0, alias="JAVA_API_TIMEOUT")
    java_api_token: str | None = Field(default=None, alias="JAVA_API_TOKEN")

    postgres_uri: str = Field(
        default="postgresql://customer_agent:customer_agent_pwd@127.0.0.1:5432/customer_agent_memory?sslmode=disable",
        validation_alias=AliasChoices("POSTGRES_URI", "POSTGRES_URL", "DATABASE_URL"),
    )

    app_name: str = "基于 LangGraph 的智能客服 Agent 系统"
    cors_origins: list[str] = ["*"]
    default_max_retries: int = 2
    log_level: str = "INFO"
    log_file: str = "app.log"
    log_max_bytes: int = 5 * 1024 * 1024
    log_backup_count: int = 3

    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )



@lru_cache
def get_settings() -> Settings:
    return Settings()
