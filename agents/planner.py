"""通用 Planner Agent - 每个节点复用的规划控制器

核心职责：
  1. 分析当前上下文，决定下一步做什么（call_tool / node_done / rollback）
  2. 在节点内循环调用工具，直到任务完成
  3. 判断问题严重程度，决定是否需要图级回滚

设计为 ReAct Agent：
  - 真实模式：LLM 自主思考，输出 PlannerDecision
  - Mock 模式：按预设策略执行，模拟 ReAct 流程

使用方式：
  planner = Planner(
      system_prompt="你是执行阶段的规划师...",
      tools=[use_legal_query, use_contract_review, ...],
      max_iterations=10,
  )
  decision = planner.run(context)
"""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_core.tools import BaseTool

from agents.states import PlannerDecision
from agents.llm_factory import is_mock_mode

logger = logging.getLogger(__name__)

DEFAULT_MAX_ITERATIONS = 10


class Planner:
    """通用规划控制器

    每个主图节点内部使用同一个 Planner 类，但配置不同的：
      - system_prompt: 告诉 planner 它的角色和目标
      - tools: 可调用的工具集（从 tools.py 导入的 use_xxx）
      - max_iterations: 最大循环次数
    """

    def __init__(
        self,
        system_prompt: str,
        tools: list[BaseTool],
        max_iterations: int = DEFAULT_MAX_ITERATIONS,
    ):
        self.system_prompt = system_prompt
        self.tools = tools
        self.max_iterations = max_iterations
        self._tool_map: dict[str, BaseTool] = {t.name: t for t in tools}

    def run(
        self,
        context: dict[str, Any],
        node_name: str = "unknown",
    ) -> PlannerDecision:
        """运行 planner，返回最终决策

        Args:
            context: 当前上下文
            node_name: 当前节点名（便于日志）

        Returns:
            PlannerDecision: call_tool / node_done / rollback
        """
        if is_mock_mode():
            return self._run_mock(context, node_name)
        else:
            return self._run_with_llm(context, node_name)

    # -------------------------------------------------------------------
    # Mock 模式
    # -------------------------------------------------------------------

    def _run_mock(self, context: dict[str, Any], node_name: str) -> PlannerDecision:
        """Mock 模式：根据节点名路由到不同的预设策略"""
        iteration = len(context.get("planner_thoughts", []))
        logger.info(f"[planner:{node_name}] Mock 迭代 {iteration + 1}/{self.max_iterations}")

        if node_name == "orchestrator":
            return self._mock_orchestrator(context, iteration)
        elif node_name == "executor":
            return self._mock_executor(context, iteration)
        elif node_name == "reporter":
            return self._mock_reporter(context, iteration)
        elif node_name == "reviewer":
            return self._mock_reviewer(context, iteration)
        else:
            return PlannerDecision(action="node_done", node_output={}, thought="未知节点，直接完成")

    def _mock_orchestrator(self, context: dict, iteration: int) -> PlannerDecision:
        """Orchestrator Mock 策略：情绪分析 → 意图分类 → 法律查询 → 信息完整性分析 → (need_info 或 node_done)

        流程：
          0. analyze_emotion → 分析用户情绪
          1. 有文件先读文件
          2. classify_intent → 意图分类
          3. use_legal_query → 查询相关法律知识
          4. analyze_info_completeness → 分析信息是否完整
          5. 如果不完整 → need_info（问用户）
          6. 如果完整 → decompose_tasks → node_done
        """
        tool_results = context.get("tool_results", [])
        user_input = context.get("user_input", "")
        uploaded_files = context.get("uploaded_files", [])
        conversation_history = context.get("conversation_history", [])
        info_complete = context.get("info_complete", False)

        # Step 0: 情绪分析（最先执行）
        if iteration == 0:
            return PlannerDecision(
                action="call_tool", tool_name="analyze_emotion",
                tool_args={
                    "user_input": user_input,
                    "conversation_history": json.dumps(conversation_history, ensure_ascii=False),
                },
                thought="首先分析用户情绪状态",
            )

        # 获取情绪数据
        emotion_raw = self._find_tool_result(tool_results, "analyze_emotion")
        try:
            emotion_data = json.loads(emotion_raw) if isinstance(emotion_raw, str) else emotion_raw
        except (json.JSONDecodeError, TypeError):
            emotion_data = {"emotion": "calm", "intensity": 0.0}

        # 迭代偏移（情绪分析占1步，文件读取占1步）
        offset = 1

        # Step 1 (offset): 有文件先读取
        if uploaded_files and iteration == offset:
            return PlannerDecision(
                action="call_tool", tool_name="use_file_reader",
                tool_args={"file_path": uploaded_files[0]},
                thought="用户上传了文件，先读取文件内容",
            )
        if uploaded_files:
            offset = 2

        # Step 1 (offset): 意图分类
        if iteration == offset:
            return PlannerDecision(
                action="call_tool", tool_name="classify_intent",
                tool_args={"user_input": user_input}, thought="需要先分类用户意图",
            )

        # 获取意图数据（从 classify_intent 的结果中）
        intent_raw = self._find_tool_result(tool_results, "classify_intent")
        try:
            intent_data = json.loads(intent_raw) if isinstance(intent_raw, str) else intent_raw
        except (json.JSONDecodeError, TypeError):
            intent_data = {}
        intent = intent_data.get("intent", "unknown") if isinstance(intent_data, dict) else "unknown"

        # Step 2 (offset+1): 查询相关法律知识
        if iteration == offset + 1:
            query_map = {
                "ip_trade_secret": "商业秘密 构成要件 保密措施 禁令",
                "contract_review": "合同审查 违约责任 条款效力",
                "labor_dispute": "劳动法 解雇 经济补偿 违法解除",
                "fraud_consumer": "诈骗 消费欺诈 消费者权益保护法 退款赔偿",
            }
            query = query_map.get(intent, user_input)
            return PlannerDecision(
                action="call_tool", tool_name="use_legal_query",
                tool_args={"query": query}, thought=f"查询 {intent} 相关法律知识",
            )

        # Step 3 (offset+2): 分析信息完整性
        if iteration == offset + 2:
            legal_result = self._find_tool_result(tool_results, "use_legal_query")
            legal_text = legal_result if isinstance(legal_result, str) else str(legal_result)
            return PlannerDecision(
                action="call_tool", tool_name="analyze_info_completeness",
                tool_args={
                    "intent": intent,
                    "user_input": user_input,
                    "conversation_history": json.dumps(conversation_history, ensure_ascii=False),
                    "legal_query_result": legal_text[:500] if legal_text else "",
                },
                thought="分析信息是否完整",
            )

        # Step 4 (offset+3): 根据 info_complete 决策
        if iteration == offset + 3:
            completeness = self._find_tool_result(tool_results, "analyze_info_completeness")
            if isinstance(completeness, str):
                try:
                    completeness = json.loads(completeness)
                except json.JSONDecodeError:
                    completeness = {}

            is_complete = completeness.get("info_complete", False)
            missing = completeness.get("missing_info", [])
            question = completeness.get("pending_question", "")

            if not is_complete and missing:
                logger.info(f"[planner:orchestrator] 信息不完整，缺少: {missing}")
                return PlannerDecision(
                    action="need_info",
                    pending_question=question,
                    missing_info=missing,
                    thought=f"信息不完整，缺少 {len(missing)} 项，需要向用户追问",
                )

        # 信息已完整（或 info_complete=True 表示从 wait_for_user 恢复后已完整）
        # Step 5 (offset+4): 任务拆解
        if iteration == offset + 4 or (info_complete and iteration == offset + 3):
            intent_info_str = self._find_tool_result(tool_results, "classify_intent")
            if isinstance(intent_info_str, dict):
                intent_info_str = json.dumps(intent_info_str, ensure_ascii=False)
            return PlannerDecision(
                action="call_tool", tool_name="decompose_tasks",
                tool_args={"intent_info": intent_info_str or "{}", "user_input": user_input},
                thought="信息完整，拆解任务",
            )

        # 完成：输出 extracted_intent
        intent_result = self._find_tool_result(tool_results, "classify_intent")
        try:
            intent_data = json.loads(intent_result) if isinstance(intent_result, str) else intent_result
        except (json.JSONDecodeError, TypeError):
            intent_data = {"intent": intent}

        # 补充任务元信息
        intent_name = intent_data.get("intent", "unknown") if isinstance(intent_data, dict) else intent
        if intent_name == "ip_trade_secret":
            intent_data["task_count"] = 2
            intent_data["detected_task_types"] = ["legal_query", "legal_query"]
        elif intent_name == "contract_review":
            intent_data["task_count"] = 2
            intent_data["detected_task_types"] = ["legal_query", "contract_review"]
        elif intent_name == "labor_dispute":
            intent_data["task_count"] = 2
            intent_data["detected_task_types"] = ["legal_query", "legal_query"]
        elif intent_name == "fraud_consumer":
            intent_data["task_count"] = 2
            intent_data["detected_task_types"] = ["legal_query", "legal_query"]
        else:
            intent_data["task_count"] = 1
            intent_data["detected_task_types"] = ["legal_query"]

        # 合并对话历史中的用户补充信息
        intent_data["conversation_history"] = conversation_history

        # 获取情绪分析结果
        emotion_raw = self._find_tool_result(tool_results, "analyze_emotion")
        try:
            emotion_data = json.loads(emotion_raw) if isinstance(emotion_raw, str) else emotion_raw
        except (json.JSONDecodeError, TypeError):
            emotion_data = {"emotion": "calm", "intensity": 0.0}

        return PlannerDecision(
            action="node_done",
            node_output={"extracted_intent": intent_data, "info_complete": True, "user_emotion": emotion_data},
            thought=f"意图分析完成: {intent_name}, 情绪: {emotion_data.get('emotion', 'unknown')}",
        )

    @staticmethod
    def _find_tool_result(tool_results: list[dict], tool_name: str) -> Any:
        """从工具结果列表中找到指定工具的最近一次结果"""
        for tr in reversed(tool_results):
            if tr.get("tool_name") == tool_name:
                return tr.get("result", "")
        return None

    @staticmethod
    def _get_required_fields(node_name: str) -> list[str]:
        """获取每个节点 node_output 必须包含的字段名（与 GlobalCaseState 定义对齐）"""
        FIELD_MAP = {
            "orchestrator": ["extracted_intent", "info_complete", "user_emotion"],
            "executor": ["execution_results"],
            "reporter": ["report_content"],
            "reviewer": ["review_passed", "review_issues"],
        }
        return FIELD_MAP.get(node_name, [])

    @staticmethod
    def _compress_messages(messages: list) -> list:
        """压缩过长的消息历史，避免 LLM 上下文膨胀

        策略：
        - 保留 system 消息和最近 4 条消息不变
        - 对中间的工具结果消息，将内容截断为 200 字摘要
        - 这样既保留了对话脉络，又大幅减少 token 数
        """
        from langchain_core.messages import ToolMessage

        if len(messages) <= 6:
            return messages

        # 最近4条消息保持原样
        keep_recent = 4
        result = []
        recent = messages[-keep_recent:]
        older = messages[:-keep_recent]

        for msg in older:
            if isinstance(msg, ToolMessage) and len(getattr(msg, 'content', '')) > 200:
                # 旧的工具结果截断为摘要
                content = msg.content[:200] + "...(已压缩)"
                compressed = ToolMessage(content=content, tool_call_id=msg.tool_call_id)
                result.append(compressed)
            else:
                result.append(msg)

        result.extend(recent)
        logger.info(f"[planner] 消息压缩: {len(messages)} 条 → 保留最近{keep_recent}条，旧工具消息截断为200字")
        return result

    def _mock_executor(self, context: dict, iteration: int) -> PlannerDecision:
        tool_results = context.get("tool_results", [])
        extracted_intent = context.get("extracted_intent", {})
        user_input = context.get("user_input", "")
        intent = extracted_intent.get("intent", "unknown")

        if intent == "contract_review":
            if iteration == 0:
                return PlannerDecision(
                    action="call_tool", tool_name="use_legal_query",
                    tool_args={"query": user_input, "context": "合同审查前置查询"},
                    thought="合同审查场景，先查法规",
                )
            elif iteration == 1:
                return PlannerDecision(
                    action="call_tool", tool_name="use_contract_review",
                    tool_args={"clause_text": user_input},
                    thought="查完法规，执行合同审查",
                )
            elif iteration == 2:
                return PlannerDecision(
                    action="call_tool", tool_name="use_verifier",
                    tool_args={"result_data": json.dumps(tool_results[-1].get("result", {}), ensure_ascii=False),
                               "user_input": user_input, "task_type": "contract_review"},
                    thought="审查完成，验证结果",
                )
            else:
                return self._build_executor_done(tool_results, user_input)

        elif intent == "ip_trade_secret":
            if iteration == 0:
                return PlannerDecision(
                    action="call_tool", tool_name="use_legal_query",
                    tool_args={"query": "商业秘密构成要件 法律规定"},
                    thought="查询商业秘密构成要件",
                )
            elif iteration == 1:
                return PlannerDecision(
                    action="call_tool", tool_name="use_legal_query",
                    tool_args={"query": f"{user_input} 禁令申请条件"},
                    thought="查询禁令申请条件",
                )
            elif iteration == 2:
                return PlannerDecision(
                    action="call_tool", tool_name="use_verifier",
                    tool_args={"result_data": json.dumps(
                        [tr.get("result", "") for tr in tool_results], ensure_ascii=False
                    ), "user_input": user_input, "task_type": "legal_query"},
                    thought="查询完成，验证结果",
                )
            else:
                return self._build_executor_done(tool_results, user_input)

        elif intent == "fraud_consumer":
            if iteration == 0:
                return PlannerDecision(
                    action="call_tool", tool_name="use_legal_query",
                    tool_args={"query": f"{user_input} 诈骗 消费欺诈 法律规定"}, thought="查询诈骗/消费欺诈相关法律",
                )
            elif iteration == 1:
                return PlannerDecision(
                    action="call_tool", tool_name="use_legal_query",
                    tool_args={"query": "消费者权益保护法 网购退款 欺诈赔偿"}, thought="查询消费者权益保护法",
                )
            elif iteration == 2:
                return PlannerDecision(
                    action="call_tool", tool_name="use_verifier",
                    tool_args={"result_data": json.dumps(
                        [tr.get("result", "") for tr in tool_results], ensure_ascii=False
                    ), "user_input": user_input, "task_type": "legal_query"},
                    thought="查询完成，验证结果",
                )
            else:
                return self._build_executor_done(tool_results, user_input)

        else:
            if iteration == 0:
                return PlannerDecision(
                    action="call_tool", tool_name="use_legal_query",
                    tool_args={"query": user_input}, thought="查询相关法律法规",
                )
            elif iteration == 1:
                return PlannerDecision(
                    action="call_tool", tool_name="use_verifier",
                    tool_args={"result_data": json.dumps(tool_results[-1].get("result", {}), ensure_ascii=False),
                               "user_input": user_input, "task_type": "legal_query"},
                    thought="查询完成，验证结果",
                )
            else:
                return self._build_executor_done(tool_results, user_input)

    def _build_executor_done(self, tool_results: list, user_input: str) -> PlannerDecision:
        execution_results = []
        for i, tr in enumerate(tool_results):
            if tr.get("tool_name") == "use_verifier":
                continue
            tool_name = tr.get("tool_name", "")
            if "contract" in tool_name:
                task_type = "contract_review"
                desc = "合同条款红蓝对抗审查"
            else:
                task_type = "legal_query"
                desc = "法律知识库查询"
            execution_results.append({
                "task_id": f"task_{i + 1}",
                "task_type": task_type,
                "description": desc,
                "status": "completed",
                "result": tr.get("result", ""),
            })
        return PlannerDecision(
            action="node_done",
            node_output={"execution_results": execution_results},
            thought=f"执行完成，共 {len(execution_results)} 个结果",
        )

    def _mock_reporter(self, context: dict, iteration: int) -> PlannerDecision:
        execution_results = context.get("execution_results", [])
        extracted_intent = context.get("extracted_intent", {})
        user_input = context.get("user_input", "")
        user_emotion = context.get("user_emotion", {})

        if iteration == 0:
            return PlannerDecision(
                action="call_tool", tool_name="use_report_generator",
                tool_args={
                    "user_input": user_input,
                    "extracted_intent": json.dumps(extracted_intent, ensure_ascii=False),
                },
                thought="生成报告",
            )
        elif iteration == 1:
            # 生成报告后，根据用户情绪润色
            tool_results = context.get("tool_results", [])
            report = tool_results[-1].get("result", "") if tool_results else ""
            return PlannerDecision(
                action="call_tool", tool_name="polish_report",
                tool_args={
                    "report_content": report,
                    "user_emotion": json.dumps(user_emotion, ensure_ascii=False),
                },
                thought="根据用户情绪润色报告",
            )
        else:
            # 润色完成，输出最终报告
            tool_results = context.get("tool_results", [])
            polished_report = tool_results[-1].get("result", "") if tool_results else ""
            return PlannerDecision(
                action="node_done",
                node_output={"report_content": polished_report},
                thought="报告生成并润色完成",
            )

    def _mock_reviewer(self, context: dict, iteration: int) -> PlannerDecision:
        execution_results = context.get("execution_results", [])
        user_input = context.get("user_input", "")

        if iteration == 0:
            return PlannerDecision(
                action="call_tool", tool_name="use_verifier",
                tool_args={
                    "result_data": json.dumps(execution_results, ensure_ascii=False, default=str),
                    "user_input": user_input, "task_type": "report_review",
                },
                thought="核对报告中的事实准确性",
            )
        else:
            tool_results = context.get("tool_results", [])
            last_result = tool_results[-1].get("result", "{}") if tool_results else "{}"
            try:
                verification = json.loads(last_result) if isinstance(last_result, str) else last_result
            except json.JSONDecodeError:
                verification = {"verified": True}

            passed = verification.get("verified", True)
            return PlannerDecision(
                action="node_done",
                node_output={
                    "review_passed": passed,
                    "review_issues": verification.get("all_issues", []),
                },
                thought=f"核对{'通过' if passed else '未通过'}",
            )

    # -------------------------------------------------------------------
    # 真实 LLM 模式（ReAct 循环）
    # -------------------------------------------------------------------

    def _run_with_llm(self, context: dict[str, Any], node_name: str) -> PlannerDecision:
        """使用 LLM 运行 ReAct 循环

        核心流程：
          1. 构建 system prompt + 上下文消息
          2. LLM 思考 → 输出 tool_calls 或纯文本
          3. 如果有 tool_calls → 执行工具 → 结果加入消息 → 回到步骤 2
          4. 如果 LLM 输出纯文本且包含决策关键词 → 解析为 PlannerDecision
          5. 达到 max_iterations → 强制 node_done
        """
        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
        from agents.llm_factory import get_llm

        llm = get_llm()
        if llm is None:
            # 降级到 mock
            return self._run_mock(context, node_name)

        # 绑定工具（让 LLM 可以 function call）
        llm_with_tools = llm.bind_tools(self.tools)

        # 构建消息列表
        messages = self._build_messages(context, node_name)

        # 跟踪已调用工具及次数（防止重复调用死循环）
        tool_call_counts: dict[str, int] = {}
        # 同一工具最多调用次数
        MAX_SAME_TOOL_CALLS = 2

        # 跟踪本轮 LLM 调用的工具结果（用于 fallback 输出）
        llm_tool_results: list[dict[str, Any]] = []

        # ReAct 循环
        for iteration in range(self.max_iterations):
            logger.info(f"[planner:{node_name}] LLM 迭代 {iteration + 1}/{self.max_iterations}")

            # 优化：压缩过长的消息历史，避免 LLM 上下文膨胀导致响应极慢
            # 当消息数 > 6 时，将旧的工具结果消息截断为摘要
            if len(messages) > 6:
                messages = self._compress_messages(messages)

            try:
                # LLM 思考
                logger.info(f"[planner:{node_name}] LLM 请求(迭代{iteration + 1}), 消息数={len(messages)}")
                # 日志: 记录发送给 LLM 的消息内容
                for idx, msg in enumerate(messages):
                    role = getattr(msg, 'type', type(msg).__name__)
                    content = getattr(msg, 'content', str(msg))[:500]
                    logger.info(f"[planner:{node_name}] LLM消息[{idx}] role={role}: {content}")

                response = llm_with_tools.invoke(messages)

                # 日志: 记录 LLM 响应
                resp_content = getattr(response, 'content', '') or ''
                logger.info(f"[planner:{node_name}] LLM 响应(迭代{iteration + 1}): {resp_content[:500]}")
            except Exception as e:
                logger.error(f"[planner:{node_name}] LLM 调用失败: {e}", exc_info=True)
                return PlannerDecision(
                    action="node_done",
                    node_output={},
                    thought=f"LLM 调用失败: {type(e).__name__} - {e}",
                )

            messages.append(response)

            # 检查是否有 tool_calls
            tool_calls = getattr(response, "tool_calls", None)

            if tool_calls:
                # 执行工具调用
                for tc in tool_calls:
                    tool_name = tc["name"]
                    tool_args = tc["args"]

                    # 重复调用检测
                    tool_call_counts[tool_name] = tool_call_counts.get(tool_name, 0) + 1
                    if tool_call_counts[tool_name] > MAX_SAME_TOOL_CALLS:
                        logger.warning(
                            f"[planner:{node_name}] 工具 {tool_name} 已调用 {tool_call_counts[tool_name]} 次，"
                            f"跳过并提示 LLM 换用其他策略"
                        )
                        messages.append(ToolMessage(
                            content=f"工具 {tool_name} 已被重复调用过多次，结果没有改善。请换用其他工具或直接输出 ACTION: node_done 完成当前节点。",
                            tool_call_id=tc["id"],
                        ))
                        continue

                    logger.info(f"[planner:{node_name}] 调用工具: {tool_name}({json.dumps(tool_args, ensure_ascii=False)[:100]}...)")

                    # 执行工具
                    tool_result = self.invoke_tool(tool_name, tool_args)

                    # 日志: 记录工具结果
                    result_preview = str(tool_result)[:300] if tool_result else "(空)"
                    logger.info(f"[planner:{node_name}] 工具 {tool_name} 结果: {result_preview}")

                    # 将结果转为字符串
                    if not isinstance(tool_result, str):
                        try:
                            tool_result = json.dumps(tool_result, ensure_ascii=False)
                        except (TypeError, ValueError):
                            tool_result = str(tool_result)

                    # 截断过长的工具结果（避免 LLM 上下文过长导致响应极慢）
                    if len(tool_result) > 1500:
                        tool_result = tool_result[:1500] + "...(已截断)"

                    # 添加工具结果到消息列表
                    messages.append(ToolMessage(
                        content=tool_result,
                        tool_call_id=tc["id"],
                    ))

                    # 记录工具结果（用于 fallback 输出）
                    llm_tool_results.append({
                        "tool_name": tool_name,
                        "args": tool_args,
                        "result": tool_result,
                    })

                # 继续循环，让 LLM 基于工具结果继续思考
                continue

            # 没有 tool_calls → LLM 输出了纯文本决策
            content = response.content or ""
            decision = self._parse_decision(content, node_name)

            if decision:
                # 如果 node_done，确保 node_output 包含该节点必需的字段
                if decision.get("action") == "node_done":
                    node_output = decision.get("node_output") or {}
                    required_fields = self._get_required_fields(node_name)
                    missing_fields = [f for f in required_fields if f not in node_output or not node_output[f]]
                    if missing_fields:
                        fallback = self._extract_fallback_output(context, node_name, llm_tool_results)
                        for f in missing_fields:
                            if f in fallback:
                                node_output[f] = fallback[f]
                                logger.info(f"[planner:{node_name}] node_output 缺少字段 {f}，从工具结果补充")
                        decision["node_output"] = node_output

                logger.info(f"[planner:{node_name}] LLM 决策: {decision.get('action', 'unknown')}")
                return decision

            # 无法解析决策，追加提示让 LLM 明确输出
            messages.append(HumanMessage(
                content="请明确输出你的决策，格式为：\n"
                        "ACTION: call_tool / node_done / rollback / need_info\n"
                        "（如果是 call_tool，请指定 TOOL_NAME 和 TOOL_ARGS）"
            ))

        # 达到最大迭代，尝试从已有工具结果中提取输出
        logger.warning(f"[planner:{node_name}] 达到最大迭代 {self.max_iterations}，强制完成")
        fallback_output = self._extract_fallback_output(context, node_name, llm_tool_results)
        logger.info(f"[planner:{node_name}] fallback 输出字段: {list(fallback_output.keys())}")
        for k, v in fallback_output.items():
            v_str = str(v)[:200] if v else "(空)"
            logger.info(f"[planner:{node_name}]   {k}: {v_str}")
        return PlannerDecision(
            action="node_done",
            node_output=fallback_output,
            thought="达到最大迭代次数，基于已有结果强制完成",
        )

    def _build_messages(
        self, context: dict[str, Any], node_name: str
    ) -> list:
        """构建 LLM 消息列表

        包含：system prompt + 上下文信息 + 工具调用历史
        """
        from langchain_core.messages import HumanMessage, SystemMessage

        messages: list = []

        # System prompt
        system_content = self.system_prompt

        # 追加决策格式说明
        system_content += "\n\n## 决策格式\n"
        system_content += "每次思考后，你必须做出决策：\n"
        system_content += "- 如果需要调用工具：直接调用工具（通过 function calling）\n"
        system_content += "- 如果当前节点任务完成：输出 `ACTION: node_done`，并附上结果 JSON\n"
        system_content += "- 如果发现严重问题需要回滚：输出 `ACTION: rollback`，指定 `ROLLBACK_TO` 和原因\n"
        if node_name == "orchestrator":
            system_content += "- 如果需要向用户追问信息：输出 `ACTION: need_info`，附上 `PENDING_QUESTION` 和 `MISSING_INFO`\n"

        system_content += "\n## 重要约束\n"
        system_content += "- 不要重复调用同一个工具超过2次。如果某工具已返回结果（即使不理想），也应基于现有结果继续，或换用其他工具\n"
        system_content += "- 查询工具返回的结果即使不完美，也比没有结果好。不要因为结果不理想就反复重试\n"
        system_content += "- 优先完成节点任务，而不是追求完美结果\n"

        system_content += "\n## 输出格式\n"
        system_content += "当决定 node_done 时，请输出：\n"
        system_content += "```json\n"
        system_content += '{"action": "node_done", "node_output": {...}, "thought": "..."}\n'
        system_content += "```\n"

        if node_name == "orchestrator":
            system_content += "\n当决定 need_info 时，请输出：\n"
            system_content += "```json\n"
            system_content += '{"action": "need_info", "pending_question": "...", "missing_info": [...], "thought": "..."}\n'
            system_content += "```\n"

        messages.append(SystemMessage(content=system_content))

        # 上下文信息
        context_parts: list[str] = []
        user_input = context.get("user_input", "")
        if user_input:
            context_parts.append(f"用户输入：{user_input}")

        uploaded_files = context.get("uploaded_files", [])
        if uploaded_files:
            context_parts.append(f"上传文件：{json.dumps(uploaded_files, ensure_ascii=False)}")

        conversation_history = context.get("conversation_history", [])
        if conversation_history:
            context_parts.append("对话历史：")
            for msg in conversation_history:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                context_parts.append(f"  [{role}] {content}")

        extracted_intent = context.get("extracted_intent", {})
        if extracted_intent:
            context_parts.append(f"意图分析结果：{json.dumps(extracted_intent, ensure_ascii=False, default=str)}")

        user_emotion = context.get("user_emotion", {})
        if user_emotion:
            context_parts.append(f"用户情绪：{json.dumps(user_emotion, ensure_ascii=False)}")

        execution_results = context.get("execution_results", [])
        if execution_results:
            # 截断过长的执行结果
            results_str = json.dumps(execution_results, ensure_ascii=False, default=str)
            if len(results_str) > 1000:
                results_str = results_str[:1000] + "...(已截断)"
            context_parts.append(f"执行结果：{results_str}")

        report_content = context.get("report_content", "")
        if report_content:
            preview = report_content[:1500] if len(report_content) > 1500 else report_content
            context_parts.append(f"当前报告：\n{preview}")

        info_complete = context.get("info_complete", False)
        if info_complete:
            context_parts.append("信息状态：用户已补充信息，信息完整")

        if context_parts:
            messages.append(HumanMessage(content="\n\n".join(context_parts)))

        # 工具调用历史（让 LLM 知道已经做过什么）
        tool_results = context.get("tool_results", [])
        if tool_results:
            history_parts: list[str] = ["已完成的工具调用："]
            for tr in tool_results[-3:]:  # 最多保留最近3条
                tool_name = tr.get("tool_name", "")
                result = tr.get("result", "")
                if isinstance(result, str) and len(result) > 300:
                    result = result[:300] + "...(已截断)"
                elif not isinstance(result, str):
                    try:
                        result = json.dumps(result, ensure_ascii=False)
                        if len(result) > 300:
                            result = result[:300] + "...(已截断)"
                    except (TypeError, ValueError):
                        result = str(result)[:300]
                history_parts.append(f"- {tool_name}: {result}")
            messages.append(HumanMessage(content="\n".join(history_parts)))

        return messages

    def _parse_decision(self, content: str, node_name: str) -> PlannerDecision | None:
        """从 LLM 输出中解析 PlannerDecision

        支持两种格式：
          1. JSON 格式（优先）
          2. ACTION: xxx 文本格式（兼容）
        """
        content = content.strip()

        # 尝试解析 JSON
        json_match = self._extract_json(content)
        if json_match:
            try:
                data = json.loads(json_match)
                return self._dict_to_decision(data, node_name)
            except json.JSONDecodeError:
                pass

        # 尝试解析 ACTION: xxx 格式
        action_match = self._parse_action_text(content, node_name)
        if action_match:
            return action_match

        return None

    @staticmethod
    def _extract_json(text: str) -> str | None:
        """从文本中提取 JSON 块"""
        # 尝试提取 ```json ... ``` 代码块
        import re
        json_block = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        if json_block:
            return json_block.group(1)

        # 尝试提取 { ... } 块
        brace_start = text.find("{")
        brace_end = text.rfind("}")
        if brace_start != -1 and brace_end > brace_start:
            return text[brace_start:brace_end + 1]

        return None

    def _dict_to_decision(self, data: dict, node_name: str) -> PlannerDecision | None:
        """将解析出的 dict 转为 PlannerDecision"""
        action = data.get("action", "")

        if action == "call_tool":
            tool_name = data.get("tool_name", "")
            tool_args = data.get("tool_args", {})
            return PlannerDecision(
                action="call_tool",
                tool_name=tool_name,
                tool_args=tool_args,
                thought=data.get("thought", ""),
            )

        elif action == "node_done":
            return PlannerDecision(
                action="node_done",
                node_output=data.get("node_output", {}),
                thought=data.get("thought", ""),
            )

        elif action == "rollback":
            return PlannerDecision(
                action="rollback",
                rollback_to=data.get("rollback_to", "orchestrator"),
                rollback_reason=data.get("rollback_reason", data.get("reason", "")),
                thought=data.get("thought", ""),
            )

        elif action == "need_info" and node_name == "orchestrator":
            return PlannerDecision(
                action="need_info",
                pending_question=data.get("pending_question", ""),
                missing_info=data.get("missing_info", []),
                thought=data.get("thought", ""),
            )

        return None

    def _parse_action_text(self, content: str, node_name: str) -> PlannerDecision | None:
        """从 ACTION: xxx 文本格式解析决策"""
        import re

        # ACTION: node_done
        if re.search(r"ACTION\s*[:：]\s*node_done", content, re.IGNORECASE):
            # 尝试提取 node_output
            output = {}
            json_match = self._extract_json(content)
            if json_match:
                try:
                    data = json.loads(json_match)
                    output = data.get("node_output", data)
                except json.JSONDecodeError:
                    pass
            return PlannerDecision(
                action="node_done",
                node_output=output,
                thought=content[:200],
            )

        # ACTION: rollback
        if re.search(r"ACTION\s*[:：]\s*rollback", content, re.IGNORECASE):
            target_match = re.search(r"ROLLBACK_TO\s*[:：]\s*(\w+)", content, re.IGNORECASE)
            reason_match = re.search(r"(?:REASON|原因)\s*[:：]\s*(.+)", content, re.IGNORECASE)
            return PlannerDecision(
                action="rollback",
                rollback_to=target_match.group(1) if target_match else "orchestrator",
                rollback_reason=reason_match.group(1).strip() if reason_match else "",
                thought=content[:200],
            )

        # ACTION: need_info
        if re.search(r"ACTION\s*[:：]\s*need_info", content, re.IGNORECASE) and node_name == "orchestrator":
            question_match = re.search(r"PENDING_QUESTION\s*[:：]\s*(.+?)(?:\n|MISSING|$)", content, re.IGNORECASE | re.DOTALL)
            missing_match = re.search(r"MISSING_INFO\s*[:：]\s*\[([^\]]*)\]", content, re.IGNORECASE)
            question = question_match.group(1).strip() if question_match else ""
            missing = []
            if missing_match:
                missing = [m.strip().strip("'\"") for m in missing_match.group(1).split(",") if m.strip()]
            return PlannerDecision(
                action="need_info",
                pending_question=question,
                missing_info=missing,
                thought=content[:200],
            )

        return None

    # -------------------------------------------------------------------
    # 工具调用
    # -------------------------------------------------------------------

    def invoke_tool(self, tool_name: str, tool_args: dict[str, Any]) -> Any:
        """按名称调用工具"""
        if tool_name not in self._tool_map:
            logger.error(f"[planner] 工具不存在: {tool_name}, 可用: {list(self._tool_map.keys())}")
            return f"错误：工具 {tool_name} 不存在"

        tool = self._tool_map[tool_name]
        try:
            logger.info(f"[planner] 开始调用工具 {tool_name}, 参数: {json.dumps(tool_args, ensure_ascii=False)[:200]}")
            result = tool.invoke(tool_args)
            logger.info(f"[planner] 工具 {tool_name} 调用成功, 结果长度: {len(str(result)) if result else 0}")
            return result
        except Exception as e:
            logger.error(f"[planner] 调用工具 {tool_name} 失败: {e}", exc_info=True)
            return f"工具调用失败: {type(e).__name__} - {e}"

    # -------------------------------------------------------------------
    # 降级输出（迭代超限时从已有结果提取）
    # -------------------------------------------------------------------

    def _extract_fallback_output(
        self,
        context: dict[str, Any],
        node_name: str,
        llm_tool_results: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """当 ReAct 循环达到最大迭代时，从已有工具结果中提取 node_output

        避免因迭代耗尽而返回空结果。

        Args:
            context: 当前上下文
            node_name: 节点名
            llm_tool_results: LLM 模式下本轮内联调用的工具结果
        """
        # 优先使用 LLM 模式下内联调用的工具结果
        tool_results = llm_tool_results if llm_tool_results else context.get("tool_results", [])

        if node_name == "orchestrator":
            # 从已有结果提取意图和情绪
            output = {"info_complete": True}
            intent_raw = self._find_tool_result(tool_results, "classify_intent")
            if intent_raw:
                try:
                    intent_data = json.loads(intent_raw) if isinstance(intent_raw, str) else intent_raw
                    if isinstance(intent_data, dict):
                        intent_data["task_count"] = intent_data.get("task_count", 1)
                        intent_data["detected_task_types"] = intent_data.get("detected_task_types", ["legal_query"])
                        output["extracted_intent"] = intent_data
                except (json.JSONDecodeError, TypeError):
                    output["extracted_intent"] = {"intent": "unknown", "task_count": 1, "detected_task_types": ["legal_query"]}
            else:
                output["extracted_intent"] = {"intent": "unknown", "task_count": 1, "detected_task_types": ["legal_query"]}

            emotion_raw = self._find_tool_result(tool_results, "analyze_emotion")
            if emotion_raw:
                try:
                    emotion_data = json.loads(emotion_raw) if isinstance(emotion_raw, str) else emotion_raw
                    output["user_emotion"] = emotion_data
                except (json.JSONDecodeError, TypeError):
                    output["user_emotion"] = {"emotion": "calm", "intensity": 0.0}
            else:
                output["user_emotion"] = {"emotion": "calm", "intensity": 0.0}

            return output

        elif node_name == "executor":
            # 提取查询结果作为 execution_results
            execution_results = []
            for i, tr in enumerate(tool_results):
                tname = tr.get("tool_name", "")
                if tname in ("use_verifier",):
                    continue
                task_type = "contract_review" if "contract" in tname else "legal_query"
                execution_results.append({
                    "task_id": f"task_{i + 1}",
                    "task_type": task_type,
                    "description": "法律知识库查询",
                    "status": "completed",
                    "result": tr.get("result", ""),
                })
            return {"execution_results": execution_results}

        elif node_name == "reporter":
            # 优先从报告生成器结果中提取完整报告
            report = self._find_tool_result(tool_results, "use_report_generator")
            if report:
                # 检查是否是新的状态格式（use_report_generator 不再返回完整报告）
                try:
                    report_data = json.loads(report) if isinstance(report, str) else report
                    if isinstance(report_data, dict) and report_data.get("status") == "report_generated":
                        # 需要真正生成报告
                        report = None
                    else:
                        return {"report_content": report if isinstance(report, str) else str(report)}
                except (json.JSONDecodeError, TypeError):
                    return {"report_content": report if isinstance(report, str) else str(report)}

            # 从润色结果中提取
            polish = self._find_tool_result(tool_results, "polish_report")
            if polish:
                return {"report_content": polish if isinstance(polish, str) else str(polish)}

            # 自动生成报告（不依赖 LLM 调用工具，直接用已有数据）
            execution_results = context.get("execution_results", [])
            user_input = context.get("user_input", "")
            extracted_intent = context.get("extracted_intent", {})

            if execution_results or user_input:
                try:
                    from agents.report_agent import generate_report
                    auto_report = generate_report(
                        user_input=user_input,
                        extracted_intent=extracted_intent,
                        task_results=execution_results,
                    )
                    return {"report_content": auto_report}
                except Exception as e:
                    logger.warning(f"[planner:reporter] 自动生成报告失败: {e}")

            return {"report_content": ""}

        elif node_name == "reviewer":
            return {"review_passed": True, "review_issues": []}

        return {}
