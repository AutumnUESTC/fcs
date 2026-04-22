"""法律多智能体系统 - 主控工作流 (Main Orchestrator)

图结构：
  START → orchestrator → executor → reporter → reviewer → END
               │              ↑           ↑          │
               ├→ END          └───────────┴──────────┘
          (need_info)                    (rollback 条件边)

多轮对话机制（不使用 interrupt）：
  - orchestrator 判断信息不足 → 设置 pending_question + 路由到 END
  - API 层检测 pending_question → 返回 status="need_info"
  - 用户回复后，API 层把对话历史拼入 user_input 重新跑图
  - orchestrator 检测到 conversation_history 有追问记录 → 跳过追问，继续执行

orchestrator 第一步执行 analyze_emotion 分析用户情绪，结果写入 state.user_emotion。
reporter 生成报告后调用 polish_report 根据情绪润色报告。

每个节点内部是一个子图（planner 循环），结构相同但工具集不同：
  - orchestrator: analyze_emotion + classify_intent + decompose_tasks + use_file_reader + use_legal_query + analyze_info_completeness
  - executor: use_legal_query + use_contract_review + use_verifier
  - reporter: use_report_generator + polish_report
  - reviewer: use_verifier
"""

from __future__ import annotations

import logging
from typing import Any

from langgraph.graph import END, StateGraph

from agents.planner import Planner
from agents.node_subgraph import build_node_subgraph, extract_node_output
from agents.states import GlobalCaseState, NodeSubState
from agents.tools import (
    use_legal_query,
    use_contract_review,
    use_verifier,
    use_report_generator,
    use_file_reader,
    analyze_info_completeness,
    analyze_emotion,
    polish_report,
)
from agents.orchestrator_agent import classify_intent, decompose_tasks

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 各节点的 Planner 配置
# ---------------------------------------------------------------------------


ORCHESTRATOR_PLANNER = Planner(
    system_prompt=(
        "你是法律意图分析规划师。你的任务是：\n"
        "1. 分析用户的情绪状态，了解用户的心理状态\n"
        "2. 分析用户的法律诉求，判断意图类型\n"
        "3. 查询相关法律知识，了解该类案件需要的关键信息\n"
        "4. 分析用户已提供的信息是否完整\n"
        "5. 信息完整后，将诉求拆解为可执行的子任务列表\n"
        "可用工具：analyze_emotion, classify_intent, decompose_tasks, use_file_reader, use_legal_query, analyze_info_completeness\n"
        "重要：绝对不要假设用户上传了文件。只有在用户明确说'我上传了文件'或'这是文件'且提供了具体文件路径时，才调用 use_file_reader。如果用户只是提到合同、协议等关键词，但没有提供文件路径，不要调用 use_file_reader。\n"
        "请依次调用工具完成分析。第一步务必调用 analyze_emotion 分析用户情绪。\n\n"
        "## 追问规则（非常重要）\n"
        "在调用 analyze_info_completeness 之后，必须判断信息是否完整。\n"
        "以下情况必须使用 need_info 动作向用户追问：\n"
        "- 用户只说了模糊诉求（如'我需要法律援助'、'我要打官司'、'我被骗了'），没有说明具体事实\n"
        "- 缺少关键事实：事件经过、涉及金额、对方身份、时间节点等\n"
        "- 缺少具体诉求：想要赔偿、想要起诉、想要调解等\n"
        "- 用户输入少于15个字且未包含具体案件事实\n\n"
        "只有在用户提供了足够具体的事实和诉求时，才能输出 node_done。\n"
        "追问时 pending_question 必须明确告诉用户需要补充什么信息，missing_info 列出缺失的关键信息项。\n\n"
        "## node_done 输出格式要求\n"
        "当输出 ACTION: node_done 时，node_output 必须严格包含以下字段：\n"
        "```json\n"
        '{"action": "node_done", "node_output": {\n'
        '  "extracted_intent": {"intent": "意图名", "domain": "领域", "confidence": 0.8, "task_count": 2, "detected_task_types": ["legal_query", "contract_review"]},\n'
        '  "info_complete": true,\n'
        '  "user_emotion": {"emotion": "情绪", "intensity": 0.5, "keywords": ["关键词"], "suggestion": "建议"}\n'
        '}, "thought": "..."}\n'
        "```\n"
        "extracted_intent 是必须的，来自 classify_intent 工具结果。user_emotion 来自 analyze_emotion 工具结果。"
    ),
    tools=[analyze_emotion, classify_intent, decompose_tasks, use_file_reader, use_legal_query, analyze_info_completeness],
    max_iterations=10,
)

EXECUTOR_PLANNER = Planner(
    system_prompt=(
        "你是法律任务执行规划师。你的任务是：\n"
        "1. 根据意图分析结果，规划执行步骤\n"
        "2. 调用法律查询、合同审查等工具执行任务\n"
        "3. 验证执行结果是否准确\n"
        "4. 如果结果有问题，重新执行或调整策略\n"
        "可用工具：use_legal_query, use_contract_review, use_verifier\n"
        "如果发现意图分析有严重错误，可以决定回滚到 orchestrator 节点。\n\n"
        "## node_done 输出格式要求\n"
        "当输出 ACTION: node_done 时，node_output 必须严格包含以下字段：\n"
        "```json\n"
        '{"action": "node_done", "node_output": {\n'
        '  "execution_results": [\n'
        '    {"task_id": "task_1", "task_type": "legal_query", "description": "查询描述", "status": "completed", "result": "查询结果"}\n'
        '  ]\n'
        '}, "thought": "..."}\n'
        "```\n"
        "execution_results 是必须的，每个元素包含 task_id, task_type, description, status, result。把所有工具调用结果汇总到 execution_results 中。"
    ),
    tools=[use_legal_query, use_contract_review, use_verifier],
    max_iterations=10,
)

REPORTER_PLANNER = Planner(
    system_prompt=(
        "你是法律报告生成规划师。你的任务是：\n"
        "1. 调用 use_report_generator 生成法律分析报告（只需传 user_input 和 extracted_intent，系统会自动补充执行结果）\n"
        "2. 调用 polish_report 根据用户情绪润色报告\n"
        "3. 如果报告质量满意，输出 node_done\n"
        "可用工具：use_report_generator, polish_report\n"
        "重要：use_report_generator 不需要传 execution_results 参数，系统会自动获取。\n"
        "如果发现执行结果有严重问题，可以决定回滚到 executor 节点。\n\n"
        "## node_done 输出格式要求\n"
        "当输出 ACTION: node_done 时，node_output 必须严格包含以下字段：\n"
        "```json\n"
        '{"action": "node_done", "node_output": {\n'
        '  "report_content": "完整的法律分析报告文本（markdown格式）"\n'
        '}, "thought": "..."}\n'
        "```\n"
        "report_content 是必须的，内容为最终生成的完整法律分析报告。"
    ),
    tools=[use_report_generator, polish_report],
    max_iterations=3,
)

REVIEWER_PLANNER = Planner(
    system_prompt=(
        "你是法律报告审核规划师。你的任务是：\n"
        "1. 核对报告中的法条引用是否正确\n"
        "2. 检查逻辑一致性\n"
        "3. 评估报告整体质量\n"
        "可用工具：use_verifier\n"
        "如果发现法条引用有严重错误，可以决定回滚到 executor 甚至 orchestrator 节点。\n\n"
        "## node_done 输出格式要求\n"
        "当输出 ACTION: node_done 时，node_output 必须严格包含以下字段：\n"
        "```json\n"
        '{"action": "node_done", "node_output": {\n'
        '  "review_passed": true,\n'
        '  "review_issues": ["问题1", "问题2"]\n'
        '}, "thought": "..."}\n'
        "```\n"
        "review_passed 是必须的布尔值（true=通过，false=未通过）。review_issues 是发现的问题列表，没有问题则为空数组。"
    ),
    tools=[use_verifier, use_legal_query],
    max_iterations=5,
)


# ---------------------------------------------------------------------------
# 编译子图实例
# ---------------------------------------------------------------------------


orchestrator_subgraph = build_node_subgraph("orchestrator", ORCHESTRATOR_PLANNER)
executor_subgraph = build_node_subgraph("executor", EXECUTOR_PLANNER)
reporter_subgraph = build_node_subgraph("reporter", REPORTER_PLANNER)
reviewer_subgraph = build_node_subgraph("reviewer", REVIEWER_PLANNER)


# ---------------------------------------------------------------------------
# 主图节点函数（包装子图调用）
# ---------------------------------------------------------------------------


def orchestrator_node(state: GlobalCaseState) -> dict[str, Any]:
    """orchestrator 节点：情绪分析 + 意图分析 + 信息收集"""
    logger.info("[orchestrator] 开始意图分析")

    # 构建子图输入
    sub_input: NodeSubState = {
        "user_input": state.get("user_input", ""),
        "uploaded_files": state.get("uploaded_files", []),
        "conversation_history": state.get("conversation_history", []),
        "info_complete": state.get("info_complete", False),
        "extracted_intent": state.get("extracted_intent", {}),
        "user_emotion": state.get("user_emotion", {}),
        "execution_results": [],
        "report_content": "",
        "planner_thoughts": [],
        "tool_results": [],
    }

    # 调用子图
    sub_result = orchestrator_subgraph.invoke(sub_input)

    # 提取输出
    output = extract_node_output(sub_result)
    output["rollback_signal"] = None  # 清除回滚信号，避免无限循环

    # 追问相关状态修复
    # 如果用户已经回复过追问（conversation_history 有 agent 消息 或 info_complete=True），
    # 即使子图 LLM 又输出了 need_info，也不能再追问，强制继续执行
    conversation_history = state.get("conversation_history", [])
    already_asked = any(msg.get("role") == "agent" for msg in conversation_history)
    info_complete_before = state.get("info_complete", False)

    if already_asked or info_complete_before:
        # 用户已回复过追问，覆盖子图的追问输出，强制继续
        if output.get("pending_question"):
            logger.info("[orchestrator] 用户已回复追问，忽略子图的 need_info，强制继续执行")
        output["pending_question"] = ""
        output["missing_info"] = []
        output["info_complete"] = True
    else:
        # 首次追问检查：如果用户输入太模糊且 LLM 没有主动追问，强制触发
        user_input = state.get("user_input", "")
        extracted_intent = output.get("extracted_intent", {})
        intent_name = extracted_intent.get("intent", "")
        confidence = extracted_intent.get("confidence", 0)

        is_vague = (
            len(user_input) < 15
            or (confidence < 0.6 and intent_name in ("legal_consultation", "unknown", ""))
        )

        if is_vague and not output.get("pending_question"):
            output["pending_question"] = "为了给您提供更准确的法律分析，请补充以下信息："
            output["missing_info"] = ["案件的基本事实和经过", "您的具体法律诉求", "涉及的时间、金额等关键细节"]
            output["info_complete"] = False
            logger.info("[orchestrator] 用户输入模糊，强制触发追问")

    logger.info(
        f"[orchestrator] 完成: 意图={output.get('extracted_intent', {}).get('intent', 'unknown')}"
        f", 信息完整={output.get('info_complete', True)}"
    )

    return output


def executor_node(state: GlobalCaseState) -> dict[str, Any]:
    """executor 节点：任务执行"""
    logger.info("[executor] 开始执行任务")

    sub_input: NodeSubState = {
        "user_input": state.get("user_input", ""),
        "uploaded_files": state.get("uploaded_files", []),
        "extracted_intent": state.get("extracted_intent", {}),
        "execution_results": [],
        "report_content": "",
        "planner_thoughts": [],
        "tool_results": [],
    }

    sub_result = executor_subgraph.invoke(sub_input)
    output = extract_node_output(sub_result)
    output["rollback_signal"] = None  # 清除回滚信号

    logger.info(f"[executor] 完成: {len(output.get('execution_results', []))} 个结果")
    return output


def reporter_node(state: GlobalCaseState) -> dict[str, Any]:
    """reporter 节点：报告生成 + 情绪润色"""
    logger.info("[reporter] 开始生成报告")

    sub_input: NodeSubState = {
        "user_input": state.get("user_input", ""),
        "uploaded_files": state.get("uploaded_files", []),
        "extracted_intent": state.get("extracted_intent", {}),
        "execution_results": state.get("execution_results", []),
        "user_emotion": state.get("user_emotion", {}),
        "report_content": "",
        "planner_thoughts": [],
        "tool_results": [],
    }

    sub_result = reporter_subgraph.invoke(sub_input)
    output = extract_node_output(sub_result)
    output["rollback_signal"] = None  # 清除回滚信号

    # 质量检查：如果报告内容太短或看起来是占位文字，用 generate_report 强制生成
    report = output.get("report_content", "")
    is_placeholder = (
        not report
        or len(report) < 50
        or report.startswith("这是根据")
        or "生成" in report and len(report) < 100
    )
    if is_placeholder:
        logger.warning(f"[reporter] 报告质量不佳（长度={len(report)}），强制用 generate_report 生成")
        try:
            from agents.report_agent import generate_report
            auto_report = generate_report(
                user_input=state.get("user_input", ""),
                extracted_intent=state.get("extracted_intent", {}),
                task_results=state.get("execution_results", []),
            )
            if auto_report and len(auto_report) > len(report):
                output["report_content"] = auto_report
                logger.info(f"[reporter] 自动生成报告成功，长度: {len(auto_report)} 字符")
        except Exception as e:
            logger.error(f"[reporter] 自动生成报告失败: {e}")

    logger.info(f"[reporter] 完成, output 字段: {list(output.keys())}")
    if output.get("report_content"):
        logger.info(f"[reporter] 报告长度: {len(output['report_content'])} 字符")
    else:
        logger.warning("[reporter] 报告内容为空!")
    return output


def reviewer_node(state: GlobalCaseState) -> dict[str, Any]:
    """reviewer 节点：最终核对"""
    logger.info("[reviewer] 开始最终核对")

    sub_input: NodeSubState = {
        "user_input": state.get("user_input", ""),
        "uploaded_files": state.get("uploaded_files", []),
        "extracted_intent": state.get("extracted_intent", {}),
        "execution_results": state.get("execution_results", []),
        "report_content": state.get("report_content", ""),
        "planner_thoughts": [],
        "tool_results": [],
    }

    sub_result = reviewer_subgraph.invoke(sub_input)
    output = extract_node_output(sub_result)
    output["rollback_signal"] = None  # 清除回滚信号

    passed = output.get("review_passed", True)
    logger.info(f"[reviewer] 完成: {'✅ 通过' if passed else '❌ 未通过'}")
    return output


# ---------------------------------------------------------------------------
# 主图路由函数
# ---------------------------------------------------------------------------


def route_after_orchestrator(state: GlobalCaseState) -> str:
    """orchestrator 执行后路由

    - need_info → END（返回需要追问，API 层检测 pending_question）
    - rollback → 指定节点
    - 正常 → executor
    """
    # 检查是否需要追问
    pending_question = state.get("pending_question", "")
    info_complete = state.get("info_complete", False)
    conversation_history = state.get("conversation_history", [])
    already_asked = any(msg.get("role") == "agent" for msg in conversation_history)

    if pending_question and not already_asked and not info_complete:
        logger.info("[route_after_orchestrator] 路由到 END（需要追问用户）")
        return "need_info_end"

    # 检查回滚
    rollback = state.get("rollback_signal")
    if rollback and rollback.get("target"):
        target = rollback["target"]
        logger.warning(f"[route_after_orchestrator] 回滚到 {target}")
        return target

    return "next"


def route_after_node(state: GlobalCaseState) -> str:
    """每个节点执行后，检查是否需要回滚

    - 有 rollback_signal → 回到指定节点
    - 无 rollback_signal → 继续下一个节点
    """
    rollback = state.get("rollback_signal")

    if rollback and rollback.get("target"):
        target = rollback["target"]
        reason = rollback.get("reason", "")
        logger.warning(f"[route_after_node] 回滚: {reason}，回到 {target}")
        return target

    return "next"


# ---------------------------------------------------------------------------
# 主图构建
# ---------------------------------------------------------------------------


def build_main_graph() -> StateGraph:
    """构建主控工作流图（不使用 interrupt，多轮对话由 API 层控制）"""
    builder = StateGraph(GlobalCaseState)

    # 添加节点（不再有 wait_for_user 节点）
    builder.add_node("orchestrator", orchestrator_node)
    builder.add_node("executor", executor_node)
    builder.add_node("reporter", reporter_node)
    builder.add_node("reviewer", reviewer_node)

    # 设置入口
    builder.set_entry_point("orchestrator")

    # orchestrator → 条件路由（need_info → END / rollback / next → executor）
    builder.add_conditional_edges(
        "orchestrator",
        route_after_orchestrator,
        {
            "need_info_end": END,      # 需要追问，直接结束
            "next": "executor",
            "orchestrator": "orchestrator",  # 回滚到自身
        },
    )

    # executor → reporter
    builder.add_conditional_edges(
        "executor",
        route_after_node,
        {
            "next": "reporter",
            "orchestrator": "orchestrator",
            "executor": "executor",
        },
    )

    # reporter → reviewer
    builder.add_conditional_edges(
        "reporter",
        route_after_node,
        {
            "next": "reviewer",
            "orchestrator": "orchestrator",
            "executor": "executor",
            "reporter": "reporter",
        },
    )

    # reviewer → END（或回滚）
    builder.add_conditional_edges(
        "reviewer",
        route_after_node,
        {
            "next": END,
            "orchestrator": "orchestrator",
            "executor": "executor",
            "reporter": "reporter",
        },
    )

    return builder.compile()


# 模块级编译实例（不再需要 checkpointer，不使用 interrupt）
main_graph = build_main_graph()


# ---------------------------------------------------------------------------
# 本地测试（模拟多轮对话）
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    import io
    # 修复 Windows 终端 UTF-8 输出
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")

    # 第一轮：模糊输入
    print("=" * 60)
    print("主控工作流 - 多轮对话测试")
    print("=" * 60)

    print("\n--- 第一轮：模糊输入 ---")
    initial_state: GlobalCaseState = {
        "user_input": "我被骗了",
        "uploaded_files": [],
        "execution_results": [],
        "review_issues": [],
    }
    result1 = main_graph.invoke(initial_state)
    if result1.get("pending_question"):
        print(f"  需要追问: {result1['pending_question']}")
        print(f"  缺少信息: {result1['missing_info']}")

    # 第二轮：用户补充信息后重新跑
    print("\n--- 第二轮：用户补充信息 ---")
    conversation_history = [
        {"role": "agent", "content": result1.get("pending_question", "")},
        {"role": "user", "content": "我在网上买东西，卖家收了5000元后一直不发货也联系不上"},
    ]
    resume_state: GlobalCaseState = {
        "user_input": "我被骗了。我在网上买东西，卖家收了5000元后一直不发货也联系不上，已经过了两周了，我想要求退款并追究对方责任",
        "uploaded_files": [],
        "conversation_history": conversation_history,
        "info_complete": True,
        "execution_results": [],
        "review_issues": [],
    }
    result2 = main_graph.invoke(resume_state)
    print(f"  意图: {result2.get('extracted_intent', {}).get('intent', '?')}")
    print(f"  信息完整: {result2.get('info_complete', False)}")
    if result2.get("report_content"):
        print(f"  报告长度: {len(result2['report_content'])} 字符")
    if result2.get("review_passed") is not None:
        print(f"  审核通过: {'是' if result2['review_passed'] else '否'}")
