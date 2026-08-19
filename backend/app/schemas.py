from dataclasses import dataclass
from typing import Literal, Optional

from langgraph.graph import MessagesState
from pydantic import BaseModel, Field


class SourceInfo(BaseModel):
    source_type: Literal["direct", "rag", "tool", "both", "unknown"]
    source_name: Optional[str] = None
    source_content: Optional[str] = None
    relevance_score: Optional[float] = None
    timestamp: Optional[str] = None


@dataclass
class SourceChunk:
    text: str
    source: str
    chunk_id: int
    score: float


class OverAllState(MessagesState):
    question: str
    core_question: str
    answer: str
    conversation_summary: str | None

    plan_steps: list[str]
    execution_plan: list[dict]
    pending_step_ids: list[str]
    active_step_id: str | None
    step_results: dict[str, dict]
    need_clarification: bool
    clarification_question: str | None

    revision_suggestion: Optional[str]

    sources: list[SourceInfo | dict]

    retry_count: int
    max_retries: int
    need_rework: bool
    quality_feedback: Optional[str]

AgentType = Literal["direct", "product", "order", "after_sales"]
class PlanStep(BaseModel):
    id: str
    agent: AgentType
    goal: str
    depends_on: list[str] = Field(default_factory=list)

class ExecutionPlan(BaseModel):
    core_question: str
    steps: list[PlanStep] = Field(default_factory=list, max_length=4)
    need_clarification: bool = False
    clarification_question: str | None = None

class QualityScore(BaseModel):
    relevance: float = Field(description="相关性分数 0-10", ge=0, le=10)
    completeness: float = Field(description="完整性分数 0-10", ge=0, le=10)
    accuracy: float = Field(description="准确性分数 0-10", ge=0, le=10)
    clarity: float = Field(description="清晰度分数 0-10", ge=0, le=10)
    overall_score: float = Field(description="综合得分 0-10", ge=0, le=10)
    feedback: str = Field(description="改进建议")
    need_rework: bool = Field(description="是否需要返工")


class ConversationSummary(BaseModel):
    summary: str = Field(description="Concise summary of the user and assistant conversation")


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, description="用户输入")
    max_retries: int = Field(default=2, ge=0, le=5, description="质量检查最大返工次数")
    thread_id: str = Field(default="default", min_length=1, description="会话ID，用于短期记忆隔离")


class ChatResponse(BaseModel):
    answer: str
    thread_id: str
    plan_steps: list[str] = Field(default_factory=list)
    sources: list[dict] = Field(default_factory=list)
    retry_count: int = 0
    quality_feedback: str | None = None
    revision_suggestion: str | None = None


class ThreadSummary(BaseModel):
    thread_id: str
    title: str
    last_message: str
    created_at: str
    updated_at: str


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ThreadDetail(BaseModel):
    thread_id: str
    title: str | None = None
    messages: list[ChatMessage] = Field(default_factory=list)
