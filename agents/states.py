"""法律多智能体系统 - 全局状态定义

状态分层：
  - GlobalCaseState: 主工作流全局状态，贯穿所有节点
  - NodeSubState: 每个节点（子图）的内部状态
  - DraftingSubState: 红蓝对抗审查子工作流状态（保留）
  - PlannerDecision: planner 的决策输出类型
"""

from __future__ import annotations

import operator
from typing import Annotated, Any, Literal, TypedDict


def _replace_list(old: list, new: list) -> list:
    """自定义 reducer：用新列表完全替换旧列表（而非追加）"""
    return new


# ---------------------------------------------------------------------------
# Planner 决策类型
# ---------------------------------------------------------------------------


class PlannerDecision(TypedDict, total=False):
    """planner 每次思考后的决策输出

    四种 action：
      - call_tool: 继续在节点内调用工具
      - node_done: 当前节点完成，主图继续
      - rollback: 问题严重，需要回到之前的节点
      - need_info: 需要向用户补充信息（仅 orchestrator 使用）
    """

    action: Literal["call_tool", "node_done", "rollback", "need_info"]

    # action=call_tool 时
    tool_name: str
    tool_args: dict[str, Any]

    # action=node_done 时
    node_output: dict[str, Any]

    # action=rollback 时
    rollback_to: str          # 目标节点名（orchestrator / executor / reporter）
    rollback_reason: str      # 为什么回头

    # action=need_info 时
    pending_question: str     # 向用户提出的问题
    missing_info: list[str]   # 缺少的信息项（结构化，便于调试）

    # 通用
    thought: str              # planner 的思考过程（便于调试）


# ---------------------------------------------------------------------------
# 主工作流全局状态
# ---------------------------------------------------------------------------


class GlobalCaseState(TypedDict, total=False):
    """主工作流全局状态

    贯穿 orchestrator → wait_for_user → executor → reporter → reviewer 全流程。
    每个节点（子图）读取需要的字段，写回结果。
    """

    # 用户原始输入（自然语言描述的法律诉求）
    user_input: str

    # 用户上传的文件路径列表（可选）
    uploaded_files: list[str]

    # 多轮对话记录 [{"role":"agent","content":"..."}, {"role":"user","content":"..."}]
    conversation_history: Annotated[list[dict[str, str]], operator.add]

    # 当前需要问用户的问题（need_info 时设置）
    pending_question: str

    # 缺少的信息列表（need_info 时设置）
    missing_info: list[str]

    # 信息是否已周全（orchestrator 判断完成后设置）
    info_complete: bool

    # 意图解析结果，例如 {"intent": "ip_trade_secret", "domain": "ip", ...}
    extracted_intent: dict[str, Any]

    # 执行结果（executor 节点写回，使用 replace 语义避免回滚后重复）
    execution_results: Annotated[list[dict[str, Any]], _replace_list]

    # 报告内容（reporter 节点写回）
    report_content: str

    # 最终核对结果（reviewer 节点写回）
    review_passed: bool
    review_issues: list[str]

    # 回滚信号（子图写回主图的）
    # {"target": "executor", "reason": "..."} 或 None
    rollback_signal: dict[str, Any]

    # 用户情绪分析结果（orchestrator 节点写回）
    # 例如 {"emotion": "anxious", "intensity": 0.7, "keywords": ["担心", "急迫"]}
    user_emotion: dict[str, Any]

    # 当前节点内 planner 的思考历史（子图内部用，replace 语义避免跨节点累积）
    planner_thoughts: Annotated[list[dict[str, Any]], _replace_list]

    # 当前节点内的工具调用结果（子图内部用，replace 语义避免跨节点累积）
    tool_results: Annotated[list[dict[str, Any]], _replace_list]


# ---------------------------------------------------------------------------
# 节点子图内部状态
# ---------------------------------------------------------------------------


class NodeSubState(TypedDict, total=False):
    """每个节点（子图）的内部状态

    子图内部的循环状态：
      planner → (call_tool) → tool_executor → planner → ...
      planner → (node_done) → 返回主图
      planner → (rollback) → 返回主图（带回滚信号）
      planner → (need_info) → 返回主图（带待提问信息，orchestrator 专用）
    """

    # planner 的决策
    planner_decision: PlannerDecision

    # planner 的思考历史（本轮节点内累积）
    planner_thoughts: Annotated[list[dict[str, Any]], operator.add]

    # 工具调用结果（本轮节点内累积）
    tool_results: Annotated[list[dict[str, Any]], operator.add]

    # 用户原始输入（从 GlobalCaseState 传入）
    user_input: str

    # 用户上传的文件路径列表（从 GlobalCaseState 传入）
    uploaded_files: list[str]

    # 多轮对话历史（从 GlobalCaseState 传入，orchestrator 专用）
    conversation_history: list[dict[str, str]]

    # 用户情绪分析结果（从 GlobalCaseState 传入）
    user_emotion: dict[str, Any]

    # 信息是否已周全（从 GlobalCaseState 传入，orchestrator 专用）
    info_complete: bool

    # 意图解析结果（从 GlobalCaseState 传入）
    extracted_intent: dict[str, Any]

    # 执行结果（从 GlobalCaseState 传入，reporter/reviewer 用）
    execution_results: list[dict[str, Any]]

    # 报告内容（从 GlobalCaseState 传入，reviewer 用）
    report_content: str


# ---------------------------------------------------------------------------
# 红蓝对抗审查子工作流状态（保留）
# ---------------------------------------------------------------------------


class DraftingSubState(TypedDict, total=False):
    """红蓝对抗审查子工作流状态

    用于条款起草 → 红方攻击 → 蓝方防御 → 审批循环的子图。
    """

    # 当前正在审查/起草的条款文本
    current_clause: str

    # 支撑该条款的法律依据列表
    legal_evidence: list[dict[str, Any]]

    # 条款修订历史
    draft_history: Annotated[list[dict[str, Any]], operator.add]

    # 条款是否通过审查
    is_approved: bool
