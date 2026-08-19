import ast
import json
import operator
from datetime import datetime
from typing import Optional

from langchain.agents import create_agent
from langchain_core.tools import tool

from .llm import get_chat_model
from .rag import format_chunks_for_prompt, search_knowledge
from .services.after_sales import get_after_sales_service
from .services.order import get_order_service
from .services.product import get_product_service

_ALLOWED_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_ALLOWED_UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def _eval_math_expr(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BIN_OPS:
        left = _eval_math_expr(node.left)
        right = _eval_math_expr(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 10:
            raise ValueError("指数过大，已拒绝执行")
        return _ALLOWED_BIN_OPS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARY_OPS:
        return _ALLOWED_UNARY_OPS[type(node.op)](_eval_math_expr(node.operand))
    raise ValueError("只支持数字和 + - * / // % ** 以及括号")


@tool(parse_docstring=True)
def get_weather(city: str) -> str:
    """
    获取天气的工具。

    Args:
        city: 具体的城市名称。
    """
    return f"{city}天气晴朗，温度在15℃左右"


@tool(parse_docstring=True)
def calculator(expression: str) -> str:
    """
    计算基础数学表达式。

    Args:
        expression: 只包含数字、括号和基础运算符的表达式，例如 "128 * 36 + 19"。
    """
    try:
        tree = ast.parse(expression, mode="eval")
        value = _eval_math_expr(tree.body)
        return f"{expression} = {value}"
    except Exception as exc:
        return f"计算失败：{exc}"


@tool(parse_docstring=True)
def get_current_datetime() -> str:
    """查询当前本地日期和时间。"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@tool(parse_docstring=True)
def query_order_status(order_id: str) -> str:
    """
    查询订单状态。

    Args:
        order_id: 订单编号，必须是正整数。
    """
    service = get_order_service()
    return _json_tool_response(service.get_order_status(order_id))


@tool(parse_docstring=True)
def query_recent_order_stats(days: Optional[int] = 7) -> str:
    """
    查询最近一段时间的订单统计数据，适合回答最近7天订单总数、订单金额、成交金额等问题。

    Args:
        days: 最近多少天，默认7天。
    """
    service = get_order_service()
    return _json_tool_response(service.get_recent_order_stats(days or 7))


# Serialize business service results for Agent tool messages.
def _json_tool_response(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False)


@tool(parse_docstring=True)
def get_top_selling_products(limit: Optional[int] = 5) -> str:
    """
    获取按销量从高到低排序的热门商品列表，当用户询问最近热门商品、畅销商品时调用此工具

    Args:
        limit: 返回商品的数量，默认为5个
    """
    service = get_product_service()
    return _json_tool_response(service.list_top_products(limit or 5))


@tool(parse_docstring=True)
def rag_search_tool(question: str) -> str:
    """
    检索知识库并返回可供 Agent 参考的 RAG 上下文。

    Args:
        question: 需要从知识库检索的问题或关键词。
    """
    chunks = search_knowledge.invoke({"question": question})
    return format_chunks_for_prompt(chunks) or "未找到相关知识"


@tool(parse_docstring=True)
def query_product_info(keyword: str) -> str:
    """
    查询商品基础信息的工具，通过 Spring Boot 商品接口获取实时数据。

    Args:
        keyword: 商品名称、型号、品类或用户描述的商品关键词。
    """
    service = get_product_service()
    return _json_tool_response(service.search_products(keyword))


@tool(parse_docstring=True)
def query_product_recommendations(requirement: str, limit: Optional[int] = 10) -> str:
    """
    查询商品推荐结果的工具，通过 Spring Boot 商品推荐或搜索接口获取实时数据。

    Args:
        requirement: 用户对预算、用途、品牌、规格等商品需求的描述。
        limit: 返回推荐商品数量，默认10个。
    """
    service = get_product_service()
    return _json_tool_response(service.recommend_products(requirement, limit or 10))


@tool(parse_docstring=True)
def query_order_detail(order_id: str) -> str:
    """
    查询订单详情的工具，通过 Spring Boot 订单接口获取实时数据。

    Args:
        order_id: 订单编号。如果用户未提供订单编号，应先要求用户补充。
    """
    service = get_order_service()
    return _json_tool_response(service.get_order_detail(order_id))


@tool(parse_docstring=True)
def query_logistics_info(order_id: str) -> str:
    """
    查询物流信息的工具，通过 Spring Boot 订单接口获取发货和收货相关数据。

    Args:
        order_id: 订单编号。如果用户未提供订单编号，应先要求用户补充。
    """
    service = get_order_service()
    return _json_tool_response(service.get_logistics_info(order_id))


@tool(parse_docstring=True)
def query_after_sales_status(order_id: str) -> str:
    """
    查询售后状态的工具，基于 Spring Boot 订单接口返回当前可参考状态。

    Args:
        order_id: 订单编号或售后单号。如果用户未提供，应先要求用户补充。
    """
    service = get_after_sales_service()
    return _json_tool_response(service.get_after_sales_status(order_id))


@tool(parse_docstring=True)
def create_after_sales_request(request_summary: str) -> str:
    """
    创建售后申请的工具。当前 Java 后端未暴露创建售后单接口时，会返回明确的结构化失败原因。

    Args:
        request_summary: 用户售后诉求摘要，例如退款、退货、换货或维修原因。
    """
    service = get_after_sales_service()
    return _json_tool_response(service.create_after_sales_request(request_summary))


@tool(parse_docstring=True)
def query_recent_product_refund_rates(days: Optional[int] = 30, limit: Optional[int] = 10) -> str:
    """
    查询最近一段时间退款率最高的商品，适合回答哪些产品退款率最高。

    Args:
        days: 最近多少天，默认30天。
        limit: 返回商品数量，默认10个。
    """
    service = get_after_sales_service()
    return _json_tool_response(service.get_recent_product_refund_rates(days or 30, limit or 10))


@tool(parse_docstring=True)
def query_recent_category_refund_rates(days: Optional[int] = 30, limit: Optional[int] = 10) -> str:
    """
    查询最近一段时间退款率最高的商品类别，适合总结哪类商品退款率最高。

    Args:
        days: 最近多少天，默认30天。
        limit: 返回类别数量，默认10个。
    """
    service = get_after_sales_service()
    return _json_tool_response(service.get_recent_category_refund_rates(days or 30, limit or 10))


def create_direct_answer_agent():
    return create_agent(
        model=get_chat_model(),
        tools=[calculator, get_current_datetime, get_weather, rag_search_tool],
        system_prompt=(
            "你是直接回答 Agent，负责处理简单问答、常识解释、轻量计算、时间和天气等问题。"
            "必须参考用户提供的 plan_steps 执行；如果存在 revision_suggestion，要优先按建议修正。"
            "只有在明确需要知识依据时才调用 rag_search_tool，不要把 RAG 当成独立链路。"
            "回答要简洁、准确，不能编造工具结果。"
        ),
    )


def create_product_consult_agent():
    return create_agent(
        model=get_chat_model(),
        tools=[rag_search_tool, get_top_selling_products, query_product_info, query_product_recommendations],
        system_prompt=(
            "你是商品咨询 Agent，负责商品推荐、商品参数、库存、价格、适用场景和购买建议。"
            "必须参考用户提供的 plan_steps 执行；如果存在 revision_suggestion，要优先按建议修正。"
            "平台规则、商品知识和说明材料可调用 rag_search_tool；热门商品调用 get_top_selling_products，关键词推荐调用 query_product_recommendations，实时商品数据应调用商品 Java 接口工具。"
            "如果 Java 接口返回失败或暂无数据，要明确说明当前无法获取实时商品数据，不要伪造库存、价格或商品详情。"
        ),
    )


def create_order_agent():
    return create_agent(
        model=get_chat_model(),
        tools=[query_order_detail, query_logistics_info, query_recent_order_stats],
        system_prompt=(
            "你是订单 Agent，负责订单状态、支付状态、发货进度、物流轨迹和订单异常解释。"
            "必须参考用户提供的 plan_steps 执行；如果存在 revision_suggestion，要优先按建议修正。"
            "涉及订单、物流、最近订单总数和成交金额等实时数据时调用订单 Java 接口工具；最近N天订单统计调用 query_recent_order_stats。"
            "如果缺少订单号，要说明需要用户补充；Java 接口失败或无数据时不要编造订单状态。"
        ),
    )


def create_after_sales_agent():
    return create_agent(
        model=get_chat_model(),
        tools=[
            rag_search_tool,
            query_after_sales_status,
            query_recent_product_refund_rates,
            query_recent_category_refund_rates,
            create_after_sales_request,
        ],
        system_prompt=(
            "你是售后 Agent，负责退款、退货、换货、维修、售后进度和售后政策解释。"
            "必须参考用户提供的 plan_steps 执行；如果存在 revision_suggestion，要优先按建议修正。"
            "售后政策、规则和流程可调用 rag_search_tool；退款率最高商品调用 query_recent_product_refund_rates，退款率最高类别调用 query_recent_category_refund_rates，售后状态和申请提交应调用售后工具。"
            "如果 Java 尚未暴露售后创建接口，要清楚说明当前无法创建售后单，不要编造处理结果。"
        ),
    )


def create_tool_agent():
    agent_tools = [
        get_weather,
        calculator,
        get_current_datetime,
        query_order_status,
        query_recent_order_stats,
        get_top_selling_products,
    ]
    return create_agent(
        model=get_chat_model(),
        tools=agent_tools,
        system_prompt=(
            "你是一个工具调用 agent。你要根据用户问题自主选择是否调用工具，并自己生成工具参数。"
            "如果用户询问天气，请调用 get_weather；如果需要计算，请调用 calculator；"
            "如果需要当前时间，请调用 get_current_datetime；如果需要查询订单，请调用 query_order_status。"
            "如果问题和可用工具无关，就直接说明当前工具无法处理，不要编造工具结果。"
            "如果用户询问最近热门商品、畅销商品，请调用 get_top_selling_products。"
        ),
    )
