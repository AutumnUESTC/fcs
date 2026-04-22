"""校验智能体 - 对任务结果进行反思性审查与事实核查

ReAct Agent 模式：
  - LLM 自主决定调用 verify_fact_accuracy、check_logical_consistency、evaluate_result_quality
  - 当前 mock 模式：函数内部按 ReAct 流程调用工具
  - 后续接入真实 LLM：替换为 create_react_agent

@tool 函数内部调用 tools.py 的原始实现。
"""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_core.tools import tool

from agents.tools import _verify_fact, _check_consistency

logger = logging.getLogger(__name__)

MAX_RETRIES = 2


# ---------------------------------------------------------------------------
# Agent 可调用的工具（调用 tools.py 的原始实现）
# ---------------------------------------------------------------------------


@tool
def verify_fact_accuracy(result_data: str, task_type: str) -> str:
    """验证任务结果中的事实准确性，特别是法律引用的真实性。

    Args:
        result_data: 任务结果的 JSON 字符串
        task_type: 任务类型（contract_review / legal_query）

    Returns:
        校验结果 JSON 字符串
    """
    result = _verify_fact(result_data, task_type)
    return json.dumps(result, ensure_ascii=False)


@tool
def check_logical_consistency(result_data: str, user_input: str, task_type: str) -> str:
    """检查任务结果与用户诉求之间的逻辑一致性。

    Args:
        result_data: 任务结果的 JSON 字符串
        user_input: 用户原始输入
        task_type: 任务类型

    Returns:
        一致性检查结果 JSON 字符串
    """
    result = _check_consistency(result_data, user_input, task_type)
    return json.dumps(result, ensure_ascii=False)


@tool
def evaluate_result_quality(fact_check: str, consistency_check: str, retry_count: int) -> str:
    """综合评估结果质量，决定是否需要重试。

    Args:
        fact_check: verify_fact_accuracy 返回的 JSON 字符串
        consistency_check: check_logical_consistency 返回的 JSON 字符串
        retry_count: 当前已重试次数

    Returns:
        综合评估结果 JSON 字符串
    """
    fact_data = json.loads(fact_check) if isinstance(fact_check, str) else fact_check
    consistency_data = json.loads(consistency_check) if isinstance(consistency_check, str) else consistency_check

    fact_confidence = fact_data.get("confidence", 0.5)
    consistency_score = consistency_data.get("consistency_score", 0.5)
    all_issues = fact_data.get("issues", []) + consistency_data.get("issues", [])

    quality_score = 0.6 * fact_confidence + 0.4 * consistency_score
    verified = quality_score >= 0.6
    should_retry = not verified and retry_count < MAX_RETRIES

    feedback = ""
    if not verified:
        if all_issues:
            feedback = "发现以下问题需要修正：" + "；".join(all_issues)
        else:
            feedback = f"综合质量分 {quality_score:.0%} 低于阈值，建议重新执行任务"

    if not verified and retry_count >= MAX_RETRIES:
        verified = True
        feedback = f"⚠️ 已达最大重试次数({MAX_RETRIES})，带警告放行。未解决问题：{'；'.join(all_issues)}"

    return json.dumps({
        "verified": verified,
        "quality_score": round(quality_score, 2),
        "should_retry": should_retry,
        "feedback": feedback,
        "all_issues": all_issues,
    }, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Agent 调用入口
# ---------------------------------------------------------------------------


def verify_task_result(
    task_result: dict[str, Any],
    user_input: str,
    retry_count: int = 0,
) -> dict[str, Any]:
    """使用 Agent 校验单个任务结果

    ReAct 流程：
      思考1: "我需要验证事实准确性" → 调用 verify_fact_accuracy
      思考2: "我需要检查逻辑一致性" → 调用 check_logical_consistency
      思考3: "综合评估质量" → 调用 evaluate_result_quality
    """
    task_type = task_result.get("task_type", "unknown")
    task_id = task_result.get("task_id", "unknown")

    logger.info(f"[verifier_agent] Agent 开始校验任务 {task_id} (类型: {task_type}, 第 {retry_count + 1} 次执行)")

    result_data = json.dumps(task_result, ensure_ascii=False, default=str)

    # 步骤1: 事实核查
    fact_check = verify_fact_accuracy.invoke({"result_data": result_data, "task_type": task_type})

    # 步骤2: 逻辑一致性检查
    consistency_check = check_logical_consistency.invoke({
        "result_data": result_data,
        "user_input": user_input,
        "task_type": task_type,
    })

    # 步骤3: 综合评估
    evaluation = evaluate_result_quality.invoke({
        "fact_check": fact_check,
        "consistency_check": consistency_check,
        "retry_count": retry_count,
    })

    eval_data = json.loads(evaluation)

    logger.info(
        f"[verifier_agent] 任务 {task_id} 校验完成: "
        f"质量={eval_data.get('quality_score', 0):.0%}, "
        f"通过={'是' if eval_data.get('verified') else '否'}"
    )

    if eval_data.get("feedback"):
        logger.warning(f"[verifier_agent] 反馈: {eval_data['feedback']}")

    return eval_data
