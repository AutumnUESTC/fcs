"""通用节点子图构建器 - 每个主图节点内部的结构

子图内部结构（planner 循环）：
  planner_node → route_decision ──→ tool_executor ──→ planner_node (继续思考)
                       │
                       ├── action=node_done → 输出结果，返回主图
                       ├── action=rollback → 设置 rollback_signal，返回主图
                       └── action=need_info → 设置追问信息，返回主图（orchestrator 专用）

每个主图节点（orchestrator/executor/reporter/reviewer）都是这个子图的一个实例，
区别只在于：
  - planner 的 system_prompt 不同
  - 可用工具集不同
"""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_core.tools import BaseTool
from langgraph.graph import END, StateGraph

from agents.planner import Planner
from agents.states import NodeSubState, PlannerDecision

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 子图节点函数
# ---------------------------------------------------------------------------


def make_planner_node(planner: Planner, node_name: str):
    """创建 planner 节点函数（闭包，捕获 planner 和 node_name）"""

    def planner_node(state: NodeSubState) -> dict[str, Any]:
        """planner 思考节点：分析上下文，输出决策"""
        # 构建上下文
        context = {
            "user_input": state.get("user_input", ""),
            "uploaded_files": state.get("uploaded_files", []),
            "conversation_history": state.get("conversation_history", []),
            "info_complete": state.get("info_complete", False),
            "extracted_intent": state.get("extracted_intent", {}),
            "execution_results": state.get("execution_results", []),
            "report_content": state.get("report_content", ""),
            "user_emotion": state.get("user_emotion", {}),
            "planner_thoughts": state.get("planner_thoughts", []),
            "tool_results": state.get("tool_results", []),
        }

        # 调用 planner
        decision = planner.run(context=context, node_name=node_name)

        logger.info(
            f"[planner_node:{node_name}] 决策: {decision.get('action', 'unknown')}"
            + (f" → {decision.get('tool_name', '')}" if decision.get("action") == "call_tool" else "")
        )

        return {"planner_decision": decision}

    return planner_node


def make_tool_executor_node(tool_map: dict):
    """创建 tool_executor 节点函数（闭包，捕获工具映射）"""

    def tool_executor_node(state: NodeSubState) -> dict[str, Any]:
        """工具执行节点：根据 planner_decision 调用工具"""
        decision = state.get("planner_decision", {})
        tool_name = decision.get("tool_name", "")
        tool_args = decision.get("tool_args", {})
        thought = decision.get("thought", "")

        logger.info(f"[tool_executor] 调用 {tool_name}({json.dumps(tool_args, ensure_ascii=False)[:100]}...)")

        if tool_name in tool_map:
            try:
                result = tool_map[tool_name].invoke(tool_args)
                tool_result = {"tool_name": tool_name, "args": tool_args, "result": result, "success": True}
            except Exception as e:
                tool_result = {"tool_name": tool_name, "args": tool_args, "result": str(e), "success": False}
        else:
            tool_result = {"tool_name": tool_name, "args": tool_args, "result": f"工具 {tool_name} 不存在", "success": False}

        return {
            "tool_results": [tool_result],
            "planner_thoughts": [{"thought": thought, "tool_name": tool_name, "action": "call_tool"}],
        }

    return tool_executor_node


# ---------------------------------------------------------------------------
# 子图路由函数
# ---------------------------------------------------------------------------


def route_planner_decision(state: NodeSubState) -> str:
    """根据 planner 的决策路由

    - call_tool → tool_executor
    - node_done → END（返回主图）
    - rollback → END（返回主图，带回滚信号）
    - need_info → END（返回主图，带追问信息）
    """
    decision = state.get("planner_decision", {})
    action = decision.get("action", "node_done")

    if action == "call_tool":
        return "tool_executor"
    elif action in ("node_done", "rollback", "need_info"):
        return END
    else:
        logger.warning(f"[route_planner_decision] 未知 action: {action}，视为完成")
        return END


# ---------------------------------------------------------------------------
# 子图构建
# ---------------------------------------------------------------------------


def build_node_subgraph(
    node_name: str,
    planner: Planner,
) -> StateGraph:
    """构建一个节点子图

    Args:
        node_name: 节点名（orchestrator / executor / reporter / reviewer）
        planner: 配置好的 Planner 实例

    Returns:
        编译后的子图 Runnable
    """
    # 将工具映射挂到 tool_executor_node 上（闭包替代方案）
    tool_executor = make_tool_executor_node(planner._tool_map)

    builder = StateGraph(NodeSubState)

    # 添加节点
    builder.add_node("planner", make_planner_node(planner, node_name))
    builder.add_node("tool_executor", tool_executor)

    # 入口 → planner
    builder.set_entry_point("planner")

    # planner → 条件路由
    builder.add_conditional_edges(
        "planner",
        route_planner_decision,
        {"tool_executor": "tool_executor", END: END},
    )

    # tool_executor → planner（循环回去继续思考）
    builder.add_edge("tool_executor", "planner")

    return builder.compile()


# ---------------------------------------------------------------------------
# 子图结果提取
# ---------------------------------------------------------------------------


def extract_node_output(subgraph_result: dict[str, Any]) -> dict[str, Any]:
    """从子图执行结果中提取 planner 的输出

    Args:
        subgraph_result: 子图 invoke 的返回值

    Returns:
        根据 action 类型提取不同内容：
        - node_done: node_output
        - rollback: node_output + rollback_signal
        - need_info: pending_question + missing_info
    """
    decision = subgraph_result.get("planner_decision", {})
    action = decision.get("action", "node_done")

    output = decision.get("node_output", {})

    # 如果是 rollback，添加回滚信号
    if action == "rollback":
        output["rollback_signal"] = {
            "target": decision.get("rollback_to", ""),
            "reason": decision.get("rollback_reason", ""),
        }

    # 如果是 need_info，添加追问信息
    if action == "need_info":
        output["pending_question"] = decision.get("pending_question", "")
        output["missing_info"] = decision.get("missing_info", [])
        output["info_complete"] = False

    return output
