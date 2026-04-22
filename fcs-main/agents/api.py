"""法律多智能体系统 - 对外接口（支持多轮对话）

外部调用方只需 import 这个文件，通过函数即可触发完整工作流。

用法示例：
    from agents.api import analyze, multi_turn_analyze

    # 单次调用（不需要追问的场景）
    result = analyze("请帮我审查这份劳动合同")

    # 多轮对话调用（自动处理追问逻辑）
    result = multi_turn_analyze(
        "我的商业秘密被泄露了",
        on_need_info=lambda question, missing: input(question),  # 自定义用户回复函数
    )
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Callable

from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 单次调用（无多轮对话）
# ---------------------------------------------------------------------------


def analyze(user_input: str, uploaded_files: list[str] | None = None, **extra_context: Any) -> "GlobalCaseState":
    """同步执行法律分析工作流，返回最终状态

    注意：此函数不处理多轮对话。如果系统需要追问，返回的 state 中
    pending_question 不为空。建议使用 multi_turn_analyze() 替代。

    Args:
        user_input: 用户的自然语言法律诉求
        uploaded_files: 用户上传的文件路径列表（可选）
        **extra_context: 可选的额外上下文

    Returns:
        最终的 GlobalCaseState
    """
    from agents.v2.states import GlobalCaseState

    initial_state: GlobalCaseState = {
        "user_input": user_input,
        "uploaded_files": uploaded_files or [],
        "execution_results": [],
        "review_issues": [],
    }

    if extra_context:
        initial_state["shared_context"] = extra_context

    logger.info(f"[api] 开始分析: {user_input[:100]}...")

    # 不带 checkpointer 的图（不支持 interrupt 暂停/恢复）
    from agents.main_graph import build_main_graph
    graph = build_main_graph(checkpointer=None)
    result = graph.invoke(initial_state)

    logger.info("[api] 分析完成")
    return result


# ---------------------------------------------------------------------------
# 多轮对话调用
# ---------------------------------------------------------------------------


def multi_turn_analyze(
    user_input: str,
    uploaded_files: list[str] | None = None,
    on_need_info: Callable[[str, list[str]], str] | None = None,
    max_rounds: int = 5,
    session_id: str | None = None,
) -> "GlobalCaseState":
    """多轮对话执行法律分析工作流

    自动处理系统追问逻辑：
      1. 提交用户问题
      2. 如果系统返回 need_info（需要更多信息），调用 on_need_info 获取用户回复
      3. 将用户回复提交给系统继续分析
      4. 重复 2-3 直到信息完整或达到最大轮次

    Args:
        user_input: 用户的自然语言法律诉求
        uploaded_files: 用户上传的文件路径列表（可选）
        on_need_info: 当系统需要追问时的回调函数，参数为 (question, missing_info)，
                      返回用户的回复文本。默认使用 input() 从终端读取。
        max_rounds: 最大追问轮次（防止无限循环）
        session_id: 会话ID（可选，自动生成）

    Returns:
        最终的 GlobalCaseState，包含报告和审核结果
    """
    from agents.main_graph import build_main_graph
    from agents.states import GlobalCaseState

    session_id = session_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": session_id}}

    # 默认用户输入回调
    if on_need_info is None:
        on_need_info = lambda question, missing: input(f"\n🤖 {question}\n\n👤 你的回复: ")

    # 使用带 checkpointer 的图（支持 interrupt 暂停/恢复）
    graph = build_main_graph(checkpointer=MemorySaver())

    # 初始状态
    initial_state: GlobalCaseState = {
        "user_input": user_input,
        "uploaded_files": uploaded_files or [],
        "execution_results": [],
        "review_issues": [],
    }

    logger.info(f"[api:multi_turn] 开始多轮分析, session={session_id}")
    logger.info(f"[api:multi_turn] 用户输入: {user_input[:100]}...")

    # 第一轮执行
    for update in graph.stream(initial_state, config=config, stream_mode="updates"):
        for node_name, snap in update.items():
            _log_step(node_name, snap)

    # 处理追问循环
    for round_num in range(max_rounds):
        # 检查当前图状态
        state = graph.get_state(config)
        current_values = state.values or {}

        # 如果不在 interrupt（wait_for_user），说明流程已结束
        if not state.next or "wait_for_user" not in state.next:
            break

        # 获取追问信息
        pending_question = current_values.get("pending_question", "")
        missing_info = current_values.get("missing_info", [])

        logger.info(f"[api:multi_turn] 第 {round_num + 1} 轮追问")
        logger.info(f"[api:multi_turn] 问题: {pending_question[:100]}...")

        # 调用回调获取用户回复
        user_response = on_need_info(pending_question, missing_info)

        if not user_response.strip():
            logger.warning("[api:multi_turn] 用户回复为空，跳过")
            continue

        logger.info(f"[api:multi_turn] 用户回复: {user_response[:100]}...")

        # 恢复执行（使用 Command(resume=...) 传递用户回复）
        graph.invoke(Command(resume=user_response), config=config)

        # 继续流式输出
        for update in graph.stream(None, config=config, stream_mode="updates"):
            for node_name, snap in update.items():
                _log_step(node_name, snap)

    # 获取最终状态
    final_state = graph.get_state(config).values or {}

    logger.info(f"[api:multi_turn] 分析完成, session={session_id}")
    if final_state.get("report_content"):
        logger.info(f"[api:multi_turn] 报告长度: {len(final_state['report_content'])} 字符")
    if final_state.get("user_emotion"):
        emotion = final_state["user_emotion"]
        if isinstance(emotion, dict):
            logger.info(f"[api:multi_turn] 用户情绪: {emotion.get('emotion', 'unknown')} (强度: {emotion.get('intensity', 0)})")
        else:
            logger.info(f"[api:multi_turn] 用户情绪: {emotion}")

    return final_state


# ---------------------------------------------------------------------------
# 流式调用
# ---------------------------------------------------------------------------


def stream_analyze(
    user_input: str, **extra_context: Any
) -> Any:
    """流式执行法律分析工作流，逐步返回每个节点的状态更新

    注意：此函数不处理多轮对话，仅适用于不需要追问的场景。

    Args:
        user_input: 用户的自然语言法律诉求
        **extra_context: 可选的额外上下文

    Yields:
        每个节点执行后的状态更新 dict，格式为 {"node_name": {...}}
    """
    from agents.main_graph import build_main_graph
    from agents.states import GlobalCaseState

    initial_state: GlobalCaseState = {
        "user_input": user_input,
        "uploaded_files": [],
        "execution_results": [],
        "review_issues": [],
    }

    if extra_context:
        initial_state["shared_context"] = extra_context

    logger.info(f"[api] 开始流式分析: {user_input[:100]}...")

    graph = build_main_graph(checkpointer=None)
    for update in graph.stream(initial_state, stream_mode="updates"):
        yield update

    logger.info("[api] 流式分析完成")


# ---------------------------------------------------------------------------
# HTTP API 调用 demo（调用 app.py 的 FastAPI 接口）
# ---------------------------------------------------------------------------


def demo_http_api_call():
    """演示如何通过 HTTP 调用后端 API 实现多轮对话

    此函数演示了前端/后端如何通过多次 HTTP 请求
    实现工作流的追问效果。实际使用时，请先启动后端：

        python app.py

    然后在另一个终端运行此 demo。
    """
    import httpx

    BASE_URL = "http://localhost:8000"

    print("=" * 60)
    print("HTTP API 多轮对话 Demo")
    print("=" * 60)

    # ---- 第一轮请求 ----
    print("\n--- 第一轮请求（提交法律问题）---")
    first_response = httpx.post(
        f"{BASE_URL}/api/legal/analyze",
        json={
            "user_input": "我的商业秘密被前员工泄露了，我能申请禁令吗？",
            "uploaded_files": [],
        },
        timeout=60.0,
    ).json()

    print(f"Status: {first_response['status']}")
    print(f"Session ID: {first_response['session_id']}")

    if first_response["status"] == "need_info":
        print(f"\n系统追问: {first_response['pending_question']}")
        print(f"缺少信息: {first_response['missing_info']}")

        # ---- 第二轮请求（用户回复追问）----
        print("\n--- 第二轮请求（回复追问）---")
        user_reply = "我们签了保密协议，限制了系统访问权限，前员工通过拷贝U盘的方式带走了客户数据，造成了约50万的损失。"
        print(f"用户回复: {user_reply}")

        second_response = httpx.post(
            f"{BASE_URL}/api/legal/analyze",
            json={
                "session_id": first_response["session_id"],
                "user_response": user_reply,
            },
            timeout=120.0,
        ).json()

        print(f"Status: {second_response['status']}")

        if second_response["status"] == "completed":
            print(f"\n意图: {second_response.get('intent', {})}")
            print(f"情绪: {second_response.get('user_emotion', {})}")
            report = second_response.get("report_content", "(无报告)")
            print(f"\n报告:\n{report[:1500]}...")
            print(f"\n审核: {'通过' if second_response.get('review_passed') else '未通过'}")

    elif first_response["status"] == "completed":
        # 一次性完成（信息足够，无需追问）
        print(f"\n意图: {first_response.get('intent', {})}")
        print(f"情绪: {first_response.get('user_emotion', {})}")
        report = first_response.get("report_content", "(无报告)")
        print(f"\n报告:\n{report[:1500]}...")

    else:
        print(f"\n错误: {first_response}")

    print("\n" + "=" * 60)


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------


def _log_step(node_name: str, snap: dict) -> None:
    """日志输出步骤信息"""
    parts = [f"[{node_name}]"]
    if "extracted_intent" in snap:
        intent = snap["extracted_intent"]
        if isinstance(intent, dict):
            parts.append(f"意图={intent.get('intent', '?')}")
    if "user_emotion" in snap:
        emotion = snap["user_emotion"]
        if isinstance(emotion, dict):
            parts.append(f"情绪={emotion.get('emotion', '?')}")
    if "pending_question" in snap and snap.get("pending_question"):
        parts.append("需要追问")
    if "execution_results" in snap:
        parts.append(f"结果数={len(snap['execution_results'])}")
    if "report_content" in snap:
        parts.append(f"报告长度={len(snap.get('report_content', ''))}")
    if "review_passed" in snap:
        parts.append(f"审核={'通过' if snap['review_passed'] else '未通过'}")

    logger.info(" ".join(parts))


# ---------------------------------------------------------------------------
# 本地测试
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    import io
    import os
    # 确保项目根目录在 sys.path 中，解决直接运行时 ModuleNotFoundError
    _project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _project_root not in sys.path:
        sys.path.insert(0, _project_root)
    # 修复 Windows 终端 UTF-8 输出
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")

    print("=" * 60)
    print("法律多智能体系统 - 多轮对话 API Demo")
    print("=" * 60)

    # 方式1：直接使用 Python API（多轮对话）
    print("\n>>> 方式1：Python API 多轮调用 <<<\n")
    result = multi_turn_analyze(
        user_input="我的商业秘密被前员工泄露了，担心会造成很大损失，能申请禁令吗？",
        on_need_info=lambda question, missing: (
            print(f"\n🤖 系统: {question}\n"),
            "我们签了保密协议，限制了系统访问权限，前员工通过拷贝U盘的方式带走了客户数据，造成了约50万的损失。"
        )[-1],  # 模拟用户回复
    )

    print(f"\n--- 最终结果 ---")
    print(f"意图: {result.get('extracted_intent', {}).get('intent', '?')}")
    emotion = result.get('user_emotion', {})
    print(f"情绪: {emotion.get('emotion', '?')} (强度: {emotion.get('intensity', 0)})")
    report = result.get('report_content', '(无报告)')
    print(f"报告:\n{report[:2000]}")
    print(f"审核: {'通过' if result.get('review_passed') else '未通过'}")

    # 方式2：HTTP API 调用（需要先启动 app.py）
    # 取消下面注释即可测试 HTTP API
    # print("\n\n>>> 方式2：HTTP API 调用 <<<\n")
    # demo_http_api_call()
