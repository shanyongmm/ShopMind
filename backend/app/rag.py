from langchain_community.embeddings import DashScopeEmbeddings
from langchain_core.tools import tool
from pymilvus import MilvusClient

from .config import get_settings
from .schemas import SourceChunk


def get_embedding_model() -> DashScopeEmbeddings:
    settings = get_settings()
    if not settings.dashscope_api_key or not settings.embed_model_name:
        raise RuntimeError("没有在 .env 中配置 DASHSCOPE_API_KEY 或 EMBED_MODEL_NAME")
    return DashScopeEmbeddings(
        model=settings.embed_model_name,
        dashscope_api_key=settings.dashscope_api_key,
    )


def format_chunks_for_prompt(chunks: list[SourceChunk]) -> str:
    if not chunks:
        return ""
    context_parts = []
    for index, chunk in enumerate(chunks, 1):
        context_parts.append(
            f"[片段{index}] 来源：{chunk.source} | 相关度：{chunk.score:.4f}\n{chunk.text}"
        )
    return "\n\n".join(context_parts)


@tool
def search_knowledge(question: str) -> list[SourceChunk]:
    """
    根据用户问题从 Milvus 向量数据库中检索相关知识片段。

    Args:
        question: 用户的问题。
    """
    settings = get_settings()
    if not settings.milvus_url or not settings.db_name or not settings.collection:
        raise RuntimeError("没有在 .env 中配置 Milvus 连接信息")

    client = MilvusClient(settings.milvus_url)
    client.use_database(settings.db_name)

    query_vector = get_embedding_model().embed_query(question)
    results = client.search(
        collection_name=settings.collection,
        data=[query_vector],
        limit=3,
        output_fields=["text", "chunk_id", "source", "sources"],
    )

    chunks: list[SourceChunk] = []
    for hit in results[0]:
        entity = hit.get("entity", {}) if hasattr(hit, "get") else {}
        score = hit.get("distance", 0.0) if hasattr(hit, "get") else 0.0
        chunks.append(
            SourceChunk(
                text=entity.get("text", ""),
                source=entity.get("source") or entity.get("sources") or "未知来源",
                chunk_id=entity.get("chunk_id", -1),
                score=score,
            )
        )

    return chunks
