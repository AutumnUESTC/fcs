"""报告生成智能体 - 汇总任务结果，生成最终法律分析报告

ReAct 模式：
  步骤1: format_report_section(header) → 生成报告头部
  步骤2: summarize_task_result × N → 格式化每个任务结果
  步骤3: format_report_section(footer) → 生成报告尾部

@tool 函数内部调用 tools.py 的原始实现。
"""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.tools import tool

from agents.tools import _format_section, _summarize_result

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Agent 可调用的工具（调用 tools.py 的原始实现）
# ---------------------------------------------------------------------------


@tool
def format_report_section(section_type: str, title: str, content: str) -> str:
    """格式化报告的某个章节。"""
    return _format_section(section_type, title, content)


@tool
def summarize_task_result(task_type: str, task_description: str, result_data: str) -> str:
    """将单个任务结果格式化为报告段落。"""
    return _summarize_result(task_type, task_description, result_data)


# ---------------------------------------------------------------------------
# Agent 调用入口
# ---------------------------------------------------------------------------


def generate_report(
    user_input: str,
    extracted_intent: dict[str, Any],
    task_results: list[dict[str, Any]],
) -> str:
    """使用 Agent 生成最终法律分析报告

    ReAct 流程：
      思考1: "生成报告头部" → format_report_section(header)
      思考2: "格式化每个任务" → summarize_task_result × N
      思考3: "生成报告尾部" → format_report_section(footer)
    """
    logger.info(f"[report_agent] Agent 开始汇总 {len(task_results)} 个任务结果")

    # 步骤1: 生成头部
    header = format_report_section.invoke({
        "section_type": "header",
        "title": "法律智能分析报告",
        "content": "",
    })

    # 步骤2: 生成用户诉求和意图解析
    intent_section = format_report_section.invoke({
        "section_type": "body",
        "title": "用户诉求",
        "content": user_input,
    })

    intent_content = (
        f"识别到 {extracted_intent.get('task_count', 0)} 个子任务："
        f"{', '.join(extracted_intent.get('detected_task_types', []))}"
    )
    intent_analysis = format_report_section.invoke({
        "section_type": "body",
        "title": "意图解析",
        "content": intent_content,
    })

    # 步骤3: 格式化每个任务结果
    task_sections: list[str] = []
    for result in task_results:
        task_type = result.get("task_type", "unknown")
        desc = result.get("description", "")

        if task_type == "contract_review":
            approved = result.get("is_approved", False)
            rounds = result.get("review_rounds", 0)
            clause = result.get("final_clause", "")
            result_data = (
                f"- 审查结果：{'通过' if approved else '未通过'}\n"
                f"- 审查轮次：{rounds}\n"
                f"- 最终条款：{clause}"
            )
        elif task_type == "legal_query":
            # 兼容两种结构：直接的 query_result 或 result 字段
            query_result = result.get("query_result", "") or result.get("result", "")
            if isinstance(query_result, str) and len(query_result) > 300:
                query_result = query_result[:300] + "..."
            result_data = f"- 查询结果：\n{query_result}"
        else:
            raw = result.get("result", str(result))
            if isinstance(raw, str) and len(raw) > 300:
                raw = raw[:300] + "..."
            result_data = raw

        # 附加校验状态
        verification = result.get("verification", {})
        if verification:
            v_status = "✅ 已验证" if verification.get("verified", True) else "⚠️ 存在疑问"
            quality = verification.get("quality_score", 1.0)
            result_data += f"\n- 结果校验：{v_status}（质量分：{quality:.0%}）"
            issues = verification.get("issues", [])
            if issues:
                result_data += f"\n- 校验备注：{'；'.join(issues)}"

        section = summarize_task_result.invoke({
            "task_type": task_type,
            "task_description": desc,
            "result_data": result_data,
        })
        task_sections.append(section)

    # 步骤4: 生成尾部
    footer = format_report_section.invoke({
        "section_type": "footer",
        "title": "报告结束",
        "content": "",
    })

    report = "\n".join([header, intent_section, intent_analysis] + task_sections + [footer])
    logger.info("[report_agent] 报告生成完成")

    return report
