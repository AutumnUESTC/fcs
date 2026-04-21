"""调度智能体 - 意图分析与任务拆解

ReAct Agent 模式：
  - LLM 自主决定调用 classify_intent 和 decompose_tasks
  - 当前 mock 模式：函数内部按 ReAct 流程调用工具
  - 后续接入真实 LLM：将函数体替换为 create_react_agent

@tool 函数内部调用 tools.py 的原始实现（_classify_intent 等）。
"""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_core.tools import tool

from agents.tools import _classify_intent

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Agent 可调用的工具（调用 tools.py 的原始实现）
# ---------------------------------------------------------------------------


@tool
def classify_intent(user_input: str) -> str:
    """对用户的法律诉求进行意图分类。

    根据用户输入判断其法律意图类型，返回结构化 JSON。

    Args:
        user_input: 用户的原始法律诉求文本

    Returns:
        意图分类 JSON 字符串
    """
    result = _classify_intent(user_input)
    return json.dumps(result, ensure_ascii=False)


@tool
def decompose_tasks(intent_info: str, user_input: str) -> str:
    """根据意图分析结果，将用户诉求拆解为可执行的子任务列表。

    Args:
        intent_info: classify_intent 返回的意图分类 JSON 字符串
        user_input: 用户的原始输入

    Returns:
        任务列表 JSON 字符串
    """
    intent_data = json.loads(intent_info) if isinstance(intent_info, str) else intent_info
    intent = intent_data.get("intent", "legal_consultation")

    tasks: list[dict[str, Any]] = []

    if intent == "contract_review":
        tasks.append({
            "type": "contract_review",
            "description": "对用户提及的合同条款进行红蓝对抗审查",
            "clause_text": user_input,
        })

    if intent == "ip_trade_secret":
        tasks.append({
            "type": "legal_query",
            "description": "查询商业秘密/知识产权相关法律依据",
            "query": user_input,
        })

    if intent in ("legal_query", "contract_review", "labor_dispute"):
        tasks.append({
            "type": "legal_query",
            "description": "查询与用户问题相关的法律法规及司法解释",
            "query": user_input,
        })

    if intent == "labor_dispute":
        tasks.append({
            "type": "legal_query",
            "description": "查询劳动纠纷的维权流程和法律依据",
            "query": user_input,
        })

    if intent == "fraud_consumer":
        tasks.append({
            "type": "legal_query",
            "description": "查询诈骗/消费欺诈的法律规定和维权途径",
            "query": user_input,
        })
        tasks.append({
            "type": "legal_query",
            "description": "查询网购纠纷的退款和赔偿相关法律依据",
            "query": "消费者权益保护法 网购 退款 赔偿 欺诈",
        })

    if not tasks:
        tasks.append({
            "type": "legal_query",
            "description": "通用法律咨询",
            "query": user_input,
        })

    return json.dumps({"tasks": tasks}, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Agent 调用入口
# ---------------------------------------------------------------------------


def analyze_intent_with_agent(user_input: str) -> dict[str, Any]:
    """使用 Agent 分析用户意图

    ReAct 流程：
      思考1: "我需要先分类意图" → 调用 classify_intent
      思考2: "意图分类完成，需要拆解任务" → 调用 decompose_tasks
      思考3: "分析完成" → 输出结果

    Mock 模式下，由函数内部按此流程依次调用工具。
    真实模式下，由 LLM 自主决定调用顺序和参数。

    Args:
        user_input: 用户原始输入

    Returns:
        意图分析 + 任务列表
    """
    logger.info(f"[orchestrator_agent] Agent 开始分析: {user_input[:80]}...")

    # 步骤1: 思考"我需要分类意图" → 调用 classify_intent
    intent_result = classify_intent.invoke({"user_input": user_input})
    intent_info = json.loads(intent_result)

    # 步骤2: 思考"意图分类完成，需要拆解任务" → 调用 decompose_tasks
    tasks_result = decompose_tasks.invoke({
        "intent_info": intent_result,
        "user_input": user_input,
    })
    tasks_info = json.loads(tasks_result)

    # TODO: 真实 LLM 模式时，替换为：
    #   from langgraph.prebuilt import create_react_agent
    #   agent = create_react_agent(model=get_llm(), tools=[classify_intent, decompose_tasks])
    #   result = agent.invoke({"messages": [("user", f"请分析: {user_input}")]})

    logger.info(
        f"[orchestrator_agent] 意图: {intent_info.get('intent', 'unknown')}, "
        f"任务数: {len(tasks_info.get('tasks', []))}"
    )

    return {
        **intent_info,
        "tasks": tasks_info.get("tasks", []),
    }


def build_tasks_from_analysis(
    analysis: dict[str, Any],
    user_input: str,
    shared_context: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """将意图分析结果转换为完整的任务列表和意图摘要"""
    shared_context = shared_context or {}
    tasks: list[dict[str, Any]] = []

    for i, task in enumerate(analysis.get("tasks", []), 1):
        task_with_id = {"id": f"task_{i}", **task}

        if task["type"] == "contract_review" and "legal_evidence" not in task_with_id:
            task_with_id["legal_evidence"] = shared_context.get("legal_evidence", [
                {"source": "《民法典》第 577 条", "content": "当事人一方不履行合同义务或者履行合同义务不符合约定的，应当承担继续履行、采取补救措施或者赔偿损失等违约责任。"},
                {"source": "《民法典》第 585 条", "content": "当事人可以约定一方违约时应当根据违约情况向对方支付一定数额的违约金。"},
            ])

        tasks.append(task_with_id)

    extracted_intent = {
        "raw_input": user_input,
        "intent": analysis.get("intent", "unknown"),
        "domain": analysis.get("domain", "general"),
        "confidence": analysis.get("confidence", 0.0),
        "reasoning": analysis.get("reasoning", ""),
        "detected_task_types": [t["type"] for t in tasks],
        "task_count": len(tasks),
    }

    return tasks, extracted_intent
