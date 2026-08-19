from datetime import datetime
import json
import logging
from typing import Literal

from langchain.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.messages import RemoveMessage
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import REMOVE_ALL_MESSAGES

from .config import get_settings
from .llm import get_chat_model
from .memory import create_postgres_checkpointer
from .schemas import ConversationSummary, ExecutionPlan, OverAllState, QualityScore
from .tools import (
    create_after_sales_agent,
    create_direct_answer_agent,
    create_order_agent,
    create_product_consult_agent,
)


model = get_chat_model()
planner_model = model.with_structured_output(ExecutionPlan)
quality_model = model.with_structured_output(QualityScore)
memory_model = model.with_structured_output(ConversationSummary)

direct_answer_agent = create_direct_answer_agent()
product_consult_agent = create_product_consult_agent()
order_agent = create_order_agent()
after_sales_agent = create_after_sales_agent()

logger = logging.getLogger(__name__)

MEMORY_COMPACTION_THRESHOLD = 12
MEMORY_RECENT_MESSAGE_LIMIT = 6


def _json_dumps(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False)


def _chunk_text(text: str, size: int = 24):
    for index in range(0, len(text), size):
        yield text[index : index + size]


def _graph_config(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}}


def _format_recent_messages(messages: list, limit: int = 6) -> str:
    if not messages:
        return "暂无历史对话。"

    lines = []
    for message in messages[-limit:]:
        role = getattr(message, "type", None)
        content = str(getattr(message, "content", "") or "").strip()
        if not content:
            continue
        if role == "human":
            label = "用户"
        elif role == "ai":
            label = "助手"
        else:
            label = str(role or "消息")
        lines.append(f"{label}：{content}")

    return "\n".join(lines) or "暂无历史对话。"


def _is_memory_message(message) -> bool:
    return isinstance(message, (HumanMessage, AIMessage))


def _memory_messages(messages: list) -> list:
    return [message for message in messages if _is_memory_message(message)]


def _format_memory_messages(messages: list) -> str:
    lines = []
    for message in _memory_messages(messages):
        content = str(getattr(message, "content", "") or "").strip()
        if not content:
            continue
        label = "用户" if isinstance(message, HumanMessage) else "系统"
        lines.append(f"{label}：{content}")
    return "\n".join(lines) or "暂无可压缩的历史对话。"


def _format_conversation_context(state: OverAllState) -> str:
    summary = str(state.get("conversation_summary") or "").strip()
    recent_messages = _format_recent_messages(state.get("messages", []))
    if not summary:
        return recent_messages
    return f"历史摘要：\n{summary}\n\n最近历史对话：\n{recent_messages}"


# 1. Planning
def _format_plan_steps(plan_steps: list[str] | None) -> str:
    if not plan_steps:
        return "1. 理解用户问题\n2. 选择合适的 Agent 或工具\n3. 生成最终回答"
    return "\n".join(f"{index}. {step}" for index, step in enumerate(plan_steps, 1))


def _plan_step_to_dict(step) -> dict:
    if hasattr(step, "model_dump"):
        return step.model_dump()
    return dict(step)


def _normalize_step_id(step_id: str, index: int) -> str:
    cleaned = "".join(char if char.isalnum() or char in {"_", "-"} else "_" for char in step_id.strip())
    return cleaned or f"step_{index}"


def _build_fallback_plan(question: str) -> ExecutionPlan:
    lowered = question.lower()
    steps = []

    if any(keyword in question for keyword in ["商品", "产品", "价格", "库存", "推荐", "参数"]):
        steps.append({"id": "step_product", "agent": "product", "goal": "查询和整理商品相关信息", "depends_on": []})
    if any(keyword in question for keyword in ["订单", "物流", "快递", "支付", "发货", "签收"]):
        steps.append({"id": "step_order", "agent": "order", "goal": "查询和整理订单或物流相关信息", "depends_on": []})
    if any(keyword in question for keyword in ["售后", "退款", "退货", "换货", "维修", "退换"]):
        steps.append({"id": "step_after_sales", "agent": "after_sales", "goal": "查询和整理售后政策或售后进度信息", "depends_on": []})
    if not steps:
        agent = "direct"
        goal = "直接回答用户问题"
        if any(keyword in lowered for keyword in ["weather", "time", "date"]):
            goal = "调用必要工具直接回答用户问题"
        steps.append({"id": "step_direct", "agent": agent, "goal": goal, "depends_on": []})

    return ExecutionPlan(core_question=question or "未找到用户核心需求", steps=steps[:4])


def _normalize_execution_plan(plan: ExecutionPlan, question: str) -> tuple[str, list[dict], list[str]]:
    core_question = (plan.core_question or "").strip() or question or "未找到用户核心需求"
    raw_steps = [_plan_step_to_dict(step) for step in plan.steps]
    if not raw_steps:
        raw_steps = [_plan_step_to_dict(step) for step in _build_fallback_plan(question).steps]

    steps = []
    seen_ids = set()
    for index, raw_step in enumerate(raw_steps, 1):
        agent = raw_step.get("agent")
        if agent not in {"direct", "product", "order", "after_sales"}:
            continue

        step_id = _normalize_step_id(str(raw_step.get("id") or ""), index)
        if step_id in seen_ids:
            step_id = f"{step_id}_{index}"
        seen_ids.add(step_id)

        goal = str(raw_step.get("goal") or "").strip() or "完成当前业务查询并形成步骤结果"
        depends_on = [str(item) for item in raw_step.get("depends_on", []) if str(item).strip()]
        steps.append(
            {
                "id": step_id,
                "agent": agent,
                "goal": goal,
                "depends_on": depends_on,
            }
        )

    if not steps:
        fallback = _build_fallback_plan(question)
        return _normalize_execution_plan(fallback, question)

    plan_steps = [f"[{step['agent']}] {step['goal']}" for step in steps]
    return core_question, steps, plan_steps


def plan_node(state: OverAllState) -> dict:
    question = state.get("question")
    if not question:
        for message in reversed(state.get("messages", [])):
            if isinstance(message, HumanMessage):
                question = str(message.content)
                break
    question = question or ""

    previous_core_question = state.get("core_question") or "未提取"
    revision_suggestion = state.get("revision_suggestion") or "无"
    conversation_history = _format_conversation_context(state)

    prompt = f"""
你是智能客服任务规划节点，需要在一次调用中完成问题提取和可执行任务规划。

最近历史对话：
{conversation_history}

用户问题：{question}
上一次核心需求（如果有）：{previous_core_question}
返工建议：{revision_suggestion}

要求：
1. 提取一句简洁、准确的核心问题
2. 生成 1-4 个可执行步骤，每一步都必须指定 id、agent、goal、depends_on
3. agent 只能从 direct、product、order、after_sales 中选择
4. 如果返工建议不为“无”，要把修正方向体现在任务中
5. 不要生成“理解问题”“生成最终回答”这类空泛步骤
6. 如果问题涉及多个业务域，请拆成多个步骤，例如商品规则、订单状态、售后判断可以分开
7. 如果用户问题缺少关键参数导致无法执行，设置 need_clarification=true 并给出 clarification_question
"""
    plan = planner_model.invoke(
        [
            SystemMessage("你是问题提取和任务规划器，只输出结构化的可执行计划。"),
            HumanMessage(prompt),
        ]
    )
    core_question, execution_plan, plan_steps = _normalize_execution_plan(plan, question)
    pending_step_ids = [step["id"] for step in execution_plan]
    logger.info("plan_node core_question=%s execution_plan=%s", core_question, execution_plan)
    return {
        "question": question,
        "core_question": core_question,
        "plan_steps": plan_steps,
        "execution_plan": execution_plan,
        "pending_step_ids": pending_step_ids,
        "active_step_id": None,
        "step_results": {},
        "need_clarification": plan.need_clarification,
        "clarification_question": plan.clarification_question,
    }


# 2. Dispatch
def find_step(execution_plan: list[dict], step_id: str) -> dict:
    for step in execution_plan:
        if step.get("id") == step_id:
            return step
    raise ValueError(f"找不到计划步骤：{step_id}")


def dispatcher_node(state: OverAllState) -> dict:
    if state.get("need_clarification"):
        return {"active_step_id": None}

    pending = state.get("pending_step_ids", [])
    if not pending:
        return {"active_step_id": None}
    return {"active_step_id": pending[0]}


def dispatch_edge(
    state: OverAllState,
) -> Literal[
    "direct_answer_agent_node",
    "product_consult_agent_node",
    "order_agent_node",
    "after_sales_agent_node",
    "clarify_node",
    "synthesis_node",
]:
    if state.get("need_clarification"):
        return "clarify_node"

    step_id = state.get("active_step_id")
    if not step_id:
        return "synthesis_node"

    step = find_step(state.get("execution_plan", []), step_id)
    return {
        "direct": "direct_answer_agent_node",
        "product": "product_consult_agent_node",
        "order": "order_agent_node",
        "after_sales": "after_sales_agent_node",
    }[step["agent"]]


# 3. Business agent execution
def _extract_message_content(message) -> str:
    if isinstance(message, dict):
        return str(message.get("content") or "")
    return str(getattr(message, "content", "") or "")


def _extract_final_ai_content(agent_messages: list) -> str:
    for message in reversed(agent_messages):
        if isinstance(message, AIMessage) and message.content:
            return str(message.content)
        if isinstance(message, dict) and message.get("role") == "assistant" and message.get("content"):
            return str(message["content"])
    return ""


def _collect_tool_sources(agent_messages: list) -> list[dict]:
    tool_sources = []
    for message in agent_messages:
        if not isinstance(message, ToolMessage):
            continue
        tool_name = getattr(message, "name", None) or getattr(message, "tool_call_id", "tool")
        tool_sources.append(
            {
                "source_type": "rag" if tool_name == "rag_search_tool" else "tool",
                "source_name": tool_name,
                "source_content": _extract_message_content(message),
                "timestamp": datetime.now().isoformat(timespec="seconds"),
            }
        )
    return tool_sources


def extract_answer(agent_response: dict) -> str:
    agent_messages = agent_response.get("messages", [])
    return _extract_final_ai_content(agent_messages)


def collect_sources(agent_response: dict) -> list[dict]:
    agent_messages = agent_response.get("messages", [])
    return _collect_tool_sources(agent_messages)


def _format_step_results(step_results: dict[str, dict] | None) -> str:
    if not step_results:
        return "暂无已完成步骤结果。"

    lines = []
    for index, (step_id, result) in enumerate(step_results.items(), 1):
        lines.append(
            "\n".join(
                [
                    f"{index}. 步骤ID：{step_id}",
                    f"   Agent：{result.get('agent', 'unknown')}",
                    f"   目标：{result.get('goal', '')}",
                    f"   结果：{result.get('answer', '')}",
                ]
            )
        )
    return "\n".join(lines)


def build_context_from_dependencies(step: dict, step_results: dict[str, dict]) -> str:
    depends_on = step.get("depends_on") or []
    if depends_on:
        related_results = {step_id: step_results.get(step_id) for step_id in depends_on if step_results.get(step_id)}
    else:
        related_results = step_results

    return _format_step_results(related_results)


def build_step_prompt(state: OverAllState, step: dict, context: str, agent_role: str) -> str:
    question = state.get("question") or ""
    core_question = state.get("core_question") or question
    plan_steps = _format_plan_steps(state.get("plan_steps", []))
    revision_suggestion = state.get("revision_suggestion") or "无"
    conversation_history = _format_conversation_context(state)

    return f"""
你当前的身份：{agent_role}

最近历史对话：
{conversation_history}

用户原始问题：
{question}

核心需求：
{core_question}

完整任务清单：
{plan_steps}

当前执行步骤：
- 步骤ID：{step.get("id")}
- 负责 Agent：{step.get("agent")}
- 当前目标：{step.get("goal")}

已完成步骤结果：
{context}

质量返工建议 revision_suggestion：
{revision_suggestion}

请只完成“当前执行步骤”的目标。需要知识库时调用 RAG 工具，需要电商实时数据时调用对应 Java 接口工具。
回答要形成可供后续步骤或最终汇总使用的结果，不要输出内部推理过程。
"""


def _run_customer_agent(state: OverAllState, agent, agent_role: str) -> dict:
    step_id = state.get("active_step_id")
    if not step_id:
        logger.warning("%s called without active_step_id", agent_role)
        return {}

    step = find_step(state.get("execution_plan", []), step_id)
    context = build_context_from_dependencies(step, state.get("step_results", {}))
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": build_step_prompt(state, step, context, agent_role),
                }
            ]
        }
    )

    step_results = dict(state.get("step_results", {}))
    step_results[step_id] = {
        "agent": step["agent"],
        "goal": step["goal"],
        "answer": extract_answer(result) or f"{agent_role} 没有生成有效步骤结果。",
        "sources": collect_sources(result),
    }
    all_sources = (state.get("sources") or []) + step_results[step_id]["sources"]

    return {
        "step_results": step_results,
        "pending_step_ids": state.get("pending_step_ids", [])[1:],
        "sources": all_sources,
    }


def direct_answer_agent_node(state: OverAllState) -> dict:
    return _run_customer_agent(state, direct_answer_agent, "直接回答 Agent")


def product_consult_agent_node(state: OverAllState) -> dict:
    return _run_customer_agent(state, product_consult_agent, "商品咨询 Agent")


def order_agent_node(state: OverAllState) -> dict:
    return _run_customer_agent(state, order_agent, "订单 Agent")


def after_sales_agent_node(state: OverAllState) -> dict:
    return _run_customer_agent(state, after_sales_agent, "售后 Agent")


# 4. Clarification and synthesis
def clarify_node(state: OverAllState) -> dict:
    question = state.get("question", "")
    logger.info("clarify_node question=%s", question)
    clarification_question = state.get("clarification_question")
    if clarification_question:
        answer = clarification_question
    else:
        answer = f"这个问题还不够明确：{question}\n请补充你的目标、对象或必要参数，我再继续处理。"
    return {
        "answer": answer,
        "messages": [AIMessage(content=answer)],
    }


def synthesis_node(state: OverAllState) -> dict:
    question = state.get("question", "")
    core_question = state.get("core_question", "")
    plan_steps = _format_plan_steps(state.get("plan_steps", []))
    step_results = _format_step_results(state.get("step_results", {}))
    revision_suggestion = state.get("revision_suggestion") or "无"
    conversation_history = _format_conversation_context(state)

    prompt = f"""
你是智能客服最终汇总节点，需要把多个 Agent 的步骤结果整合成一个直接回复用户的答案。

最近历史对话：
{conversation_history}

用户原始问题：
{question}

核心需求：
{core_question}

任务清单：
{plan_steps}

各步骤执行结果：
{step_results}

质量返工建议：
{revision_suggestion}

要求：
1. 只输出最终给用户看的答案
2. 综合各步骤结果，避免机械罗列内部步骤
3. 如果某一步没有查到数据，要明确说明，不要编造
4. 如果 revision_suggestion 不为“无”，按建议改进表达
"""
    response = model.invoke(
        [
            SystemMessage("你是智能客服最终答案汇总器。"),
            HumanMessage(prompt),
        ]
    )
    answer = str(getattr(response, "content", "") or "").strip()
    if not answer:
        answer = "当前没有生成有效答案，请补充更多问题信息后再试。"

    logger.info("synthesis_node answer_length=%s", len(answer))
    return {
        "answer": answer,
    }


# 5. Quality check and rework
@tool(parse_docstring=True)
def llm_check(question: str, core_question: str, answer: str, plan_steps: str) -> QualityScore:
    """
    专业的智能问答测评助手，判断提供的回答是否达到标准。

    Args:
        question: 用户的问题。
        core_question: 从用户问题提取出来的主要内容。
        answer: 回答用户的问题。
        plan_steps: plan_node 生成的任务清单文本。
    """
    quality_prompt = f"""
请评估以下回答的质量：

**用户问题**：{question}
**核心需求**：{core_question}
**任务清单**：
{plan_steps}
**回答内容**：{answer}

请从以下维度评估（0-10分）：
1. 相关性：回答是否直接相关于用户问题
2. 完整性：回答是否完整覆盖了问题要点和任务清单
3. 准确性：回答内容是否准确，没有编造工具或接口结果
4. 清晰度：回答是否清晰易懂

综合得分 = (相关性 + 完整性 + 准确性 + 清晰度) / 4

同时给出可直接提交给 Agent 的返工建议，并判断是否需要返工（综合得分低于6分需要返工）。
"""
    return quality_model.invoke(
        [
            SystemMessage("你是专业的回答质量评估专家，请严格、客观地评分。"),
            HumanMessage(quality_prompt),
        ]
    )


def quality_check_node(state: OverAllState) -> dict:
    question = state.get("question", "")
    core_question = state.get("core_question", "")
    answer = state.get("answer", "")

    if not answer:
        logger.warning("quality_check_node empty_answer")
        feedback = "没有可评估的答案，需要重新生成"
        return {
            "need_rework": True,
            "quality_feedback": feedback,
            "revision_suggestion": feedback,
        }

    quality_result = llm_check.invoke(
        {
            "question": question,
            "core_question": core_question,
            "answer": answer,
            "plan_steps": _format_plan_steps(state.get("plan_steps", [])),
        }
    )
    logger.info(
        "quality_check_node score=%.2f need_rework=%s",
        quality_result.overall_score,
        quality_result.need_rework,
    )
    return {
        "need_rework": quality_result.need_rework,
        "quality_feedback": quality_result.feedback,
        "revision_suggestion": quality_result.feedback if quality_result.need_rework else None,
    }


def quality_check_edge(state: OverAllState) -> Literal["rework_node", "final_output_node"]:
    if not state.get("need_rework", False):
        return "final_output_node"

    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", get_settings().default_max_retries)
    if retry_count >= max_retries:
        return "final_output_node"
    return "rework_node"


def rework_node(state: OverAllState) -> dict:
    retry_count = state.get("retry_count", 0) + 1
    feedback = state.get("quality_feedback") or "请根据质量检查意见改进回答"
    logger.info(
        "rework_node retry_count=%s feedback=%s",
        retry_count,
        feedback,
    )
    return {
        "retry_count": retry_count,
        "revision_suggestion": feedback,
    }


def rework_dispatch_edge(
    state: OverAllState,
) -> Literal["synthesis_node"]:
    logger.info("rework_dispatch_edge target=synthesis_node")
    return "synthesis_node"


# 6. Final output
def _compress_conversation_summary(existing_summary: str, messages: list) -> str:
    prompt = f"""
请压缩下面的用户与系统对话，生成一段简洁、连续的中文会话摘要。

已有摘要：
{existing_summary or "暂无"}

即将被淘汰的旧对话：
{_format_memory_messages(messages)}

要求：
1. 合并已有摘要和旧对话，不要丢失对后续对话有帮助的事实。
2. 同时保留用户提出的需求，以及系统已经给出的结论或承诺。
3. 不要按业务类型分类，不要编造信息，不要输出分析过程。
4. 只返回摘要正文。
"""
    result = memory_model.invoke(
        [
            SystemMessage("你是负责维护客服短期会话记忆的摘要 Agent。"),
            HumanMessage(prompt),
        ]
    )
    if isinstance(result, dict):
        summary = result.get("summary", "")
    else:
        summary = getattr(result, "summary", "")
    return str(summary or "").strip()


def _final_output_memory_update(state: OverAllState, answer: str) -> dict:
    current_messages = _memory_messages(state.get("messages", []))
    final_message = AIMessage(content=answer)
    persisted_messages = current_messages + [final_message]

    if len(persisted_messages) < MEMORY_COMPACTION_THRESHOLD:
        return {"messages": [final_message]}

    old_messages = persisted_messages[:-MEMORY_RECENT_MESSAGE_LIMIT]
    recent_messages = persisted_messages[-MEMORY_RECENT_MESSAGE_LIMIT:]
    existing_summary = str(state.get("conversation_summary") or "").strip()

    try:
        summary = _compress_conversation_summary(existing_summary, old_messages)
    except Exception:
        logger.exception("conversation memory compaction failed")
        return {"messages": [final_message]}

    if not summary:
        logger.warning("conversation memory compaction returned empty summary")
        return {"messages": [final_message]}

    return {
        "messages": [
            RemoveMessage(id=REMOVE_ALL_MESSAGES),
            *recent_messages,
        ],
        "conversation_summary": summary,
    }


def final_output_node(state: OverAllState) -> dict:
    answer = state.get("answer", "")
    logger.info("final_output_node answer_length=%s", len(answer))
    memory_update = _final_output_memory_update(state, answer)
    memory_update["answer"] = answer
    return memory_update


def build_graph(checkpointer=None):
    builder = StateGraph(OverAllState)
    builder.add_node("plan_node", plan_node)
    builder.add_node("dispatcher_node", dispatcher_node)
    builder.add_node("direct_answer_agent_node", direct_answer_agent_node)
    builder.add_node("product_consult_agent_node", product_consult_agent_node)
    builder.add_node("order_agent_node", order_agent_node)
    builder.add_node("after_sales_agent_node", after_sales_agent_node)
    builder.add_node("clarify_node", clarify_node)
    builder.add_node("synthesis_node", synthesis_node)
    builder.add_node("quality_check_node", quality_check_node)
    builder.add_node("rework_node", rework_node)
    builder.add_node("final_output_node", final_output_node)

    builder.add_edge(START, "plan_node")
    builder.add_edge("plan_node", "dispatcher_node")
    builder.add_conditional_edges(
        "dispatcher_node",
        dispatch_edge,
        {
            "direct_answer_agent_node": "direct_answer_agent_node",
            "product_consult_agent_node": "product_consult_agent_node",
            "order_agent_node": "order_agent_node",
            "after_sales_agent_node": "after_sales_agent_node",
            "clarify_node": "clarify_node",
            "synthesis_node": "synthesis_node",
        },
    )

    builder.add_edge("direct_answer_agent_node", "dispatcher_node")
    builder.add_edge("product_consult_agent_node", "dispatcher_node")
    builder.add_edge("order_agent_node", "dispatcher_node")
    builder.add_edge("after_sales_agent_node", "dispatcher_node")
    builder.add_edge("clarify_node", END)
    builder.add_edge("synthesis_node", "quality_check_node")

    builder.add_conditional_edges(
        "quality_check_node",
        quality_check_edge,
        {
            "rework_node": "rework_node",
            "final_output_node": "final_output_node",
        },
    )
    builder.add_conditional_edges(
        "rework_node",
        rework_dispatch_edge,
        {
            "synthesis_node": "synthesis_node",
        },
    )
    builder.add_edge("final_output_node", END)
    return builder.compile(checkpointer=checkpointer)


graph = build_graph(checkpointer=create_postgres_checkpointer())


def _initial_state(message: str, max_retries: int | None = None) -> dict:
    settings = get_settings()
    return {
        "messages": [HumanMessage(message)],
        "question": message,
        "core_question": "",
        "answer": "",
        "plan_steps": [],
        "execution_plan": [],
        "pending_step_ids": [],
        "active_step_id": None,
        "step_results": {},
        "need_clarification": False,
        "clarification_question": None,
        "sources": [],
        "retry_count": 0,
        "max_retries": max_retries if max_retries is not None else settings.default_max_retries,
        "need_rework": False,
        "quality_feedback": None,
        "revision_suggestion": None,
    }


def ask_agent(message: str, max_retries: int | None = None, thread_id: str = "default") -> dict:
    logger.info("ask_agent start thread_id=%s message=%s", thread_id, message)
    result = graph.invoke(_initial_state(message, max_retries), config=_graph_config(thread_id))
    logger.info(
        "ask_agent done completed_steps=%s retry_count=%s",
        len(result.get("step_results", {})),
        result.get("retry_count", 0),
    )
    return result


def stream_agent_events(message: str, max_retries: int | None = None, thread_id: str = "default"):
    inputs = _initial_state(message, max_retries)

    logger.info("stream_agent_events start thread_id=%s message=%s", thread_id, message)
    final_state = {}
    yield f"event: meta\ndata: {_json_dumps({'status': 'started'})}\n\n"

    for event in graph.stream(inputs, config=_graph_config(thread_id), stream_mode="updates"):
        for node_name, node_update in event.items():
            logger.info("stream node=%s keys=%s", node_name, list(node_update.keys()))
            yield f"event: node\ndata: {_json_dumps({'node': node_name})}\n\n"
            if node_update:
                final_state.update(node_update)

    answer = final_state.get("answer", "")
    for chunk in _chunk_text(answer):
        yield f"event: token\ndata: {_json_dumps({'token': chunk})}\n\n"

    done_payload = {
        "answer": answer,
        "thread_id": thread_id,
        "plan_steps": final_state.get("plan_steps", []),
        "execution_plan": final_state.get("execution_plan", []),
        "step_results": final_state.get("step_results", {}),
        "active_step_id": final_state.get("active_step_id"),
        "pending_step_ids": final_state.get("pending_step_ids", []),
        "retry_count": final_state.get("retry_count", 0),
        "quality_feedback": final_state.get("quality_feedback"),
        "revision_suggestion": final_state.get("revision_suggestion"),
    }
    logger.info(
        "stream_agent_events done completed_steps=%s",
        len(final_state.get("step_results", {})),
    )
    yield f"event: done\ndata: {_json_dumps(done_payload)}\n\n"
