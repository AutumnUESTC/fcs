"""报告生成智能体 - 汇总任务结果，生成最终法律分析报告

流程：
  步骤1: 格式化报告头部
  步骤2: 展示用户诉求
  步骤3: LLM 生成情绪回应 + 法律分析（核心：像律师对话，不是检索罗列）
  步骤4: 格式化报告尾部
"""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.tools import tool

from agents.tools import _format_section

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Agent 可调用的工具（调用 tools.py 的原始实现）
# ---------------------------------------------------------------------------


@tool
def format_report_section(section_type: str, title: str, content: str) -> str:
    """格式化报告的某个章节。"""
    return _format_section(section_type, title, content)


# ---------------------------------------------------------------------------
# 情绪感知
# ---------------------------------------------------------------------------

# 情绪类型到中文标签的映射
_EMOTION_LABELS: dict[str, str] = {
    "anxious": "焦急",
    "fearful": "害怕",
    "sad": "难过",
    "angry": "愤怒",
    "frustrated": "沮丧",
    "confused": "困惑",
    "neutral": "平静",
}

# 情绪对应的 LLM prompt 指导
_EMOTION_PROMPT_GUIDE: dict[str, str] = {
    "anxious": (
        "用户现在很着急、焦虑。你需要在分析开头先用温和坚定的语气安抚用户，"
        "让用户知道这种情况是有法律途径可以解决的，不要慌张。"
        "整体语气要沉稳、让人安心。"
    ),
    "fearful": (
        "用户现在感到害怕、不安。你需要先鼓励用户，告诉用户法律是保护劳动者的，"
        "不用担心报复，法律会站在正义的一方。语气要温暖、有力量。"
    ),
    "sad": (
        "用户现在很伤心、难过。你需要先表达理解和共情，"
        "让用户感受到被关注和被理解，然后再引导到解决问题的方向。语气要温柔。"
    ),
    "angry": (
        "用户现在很愤怒。你需要先理解并认可用户的情绪，"
        "表示这种遭遇确实令人气愤，然后引导用户理性地通过法律途径解决问题，"
        "避免冲动行为。语气要共情但理性。"
    ),
    "frustrated": (
        "用户现在感到沮丧、无助。你需要先给予鼓励，"
        "告诉用户这种情况并不少见，很多人通过法律途径成功维权，"
        "然后提供清晰可行的步骤。语气要鼓舞人心。"
    ),
    "confused": (
        "用户现在感到困惑、不知道该怎么办。你需要用简洁清晰的语言解释情况，"
        "避免过多法律术语，给出明确的步骤指引。语气要耐心、清晰。"
    ),
    "neutral": (
        "用户情绪平稳。你可以直接进入专业分析，语气专业但友好。"
    ),
}


def _detect_emotion(user_emotion: dict[str, Any]) -> str:
    """从情绪分析结果中提取主要情绪类型。

    Args:
        user_emotion: 情绪分析结果字典，可能包含 emotion, primary_emotion 等字段

    Returns:
        情绪类型字符串（如 anxious, sad, neutral 等）
    """
    if not user_emotion:
        return "neutral"

    # 尝试多种可能的字段名
    emotion = (
        user_emotion.get("primary_emotion")
        or user_emotion.get("emotion")
        or user_emotion.get("type")
        or "neutral"
    )

    # 归一化
    emotion = str(emotion).lower().strip()
    if emotion in _EMOTION_LABELS:
        return emotion

    # 模糊匹配
    for key in _EMOTION_LABELS:
        if key in emotion or emotion in key:
            return key

    return "neutral"


# ---------------------------------------------------------------------------
# LLM 法律分析（含情绪感知）
# ---------------------------------------------------------------------------


def _llm_legal_analysis(
    user_input: str,
    query_results_text: str,
    user_emotion: dict[str, Any] | None = None,
) -> str:
    """调用 LLM 基于查询结果进行法律分析，含情绪回应和维权建议。

    Args:
        user_input: 用户原始输入
        query_results_text: 法律知识库查询结果文本
        user_emotion: 情绪分析结果

    Returns:
        LLM 生成的法律分析文本（含情绪回应、违法性判断和建议）
    """
    from agents.llm_factory import get_llm

    # 检测情绪
    emotion_type = _detect_emotion(user_emotion or {})
    emotion_label = _EMOTION_LABELS.get(emotion_type, "平静")
    emotion_guide = _EMOTION_PROMPT_GUIDE.get(emotion_type, _EMOTION_PROMPT_GUIDE["neutral"])

    logger.info(f"[report_agent] 用户情绪: {emotion_type}({emotion_label})")

    llm = get_llm()
    if llm is None:
        logger.warning("[report_agent] 无 LLM 可用，使用通用法律建议模板")
        return _fallback_analysis(user_input, emotion_type)

    prompt = f"""你是一位既专业又有温度的法律顾问。你正在和一位遇到法律问题的用户对话。

## 用户诉求
{user_input}

## 法律知识库查询结果
{query_results_text}

## 用户当前情绪
用户现在感到{emotion_label}。

{emotion_guide}

## 输出要求

请用自然、对话式的语言写一篇法律分析，不要用列表堆砌，而是像一位专业律师在和客户面对面交谈。结构如下：

**开头**：根据用户情绪，先写一段情绪回应（安抚/鼓励/共情/安慰等），1-2句话即可，不要过长，自然过渡到分析。

**法律判断**：明确告诉用户遇到的情况是否违法，用通俗的语言解释为什么。如果知识库查询结果中有相关法条，请引用。判断要干脆明确，不要含糊。

**维权建议**：给出具体可操作的建议步骤，用自然的段落描述，不是编号列表。包括：
- 应该收集哪些证据
- 可以通过哪些渠道维权
- 各渠道怎么选
- 有什么时限要注意

**相关法条**：引用最相关的法律条文，标明出处。

**结尾**：一句简短的鼓励或提醒。

注意：
1. 分析必须基于查询结果中的真实案例和法条，不要凭空编造法条
2. 判断要明确，不能说"可能违法"要直接说"违法"或"不违法"
3. 建议要具体可操作
4. 整体风格是专业律师和客户对话，不是冷冰冰的报告
5. 不要出现"根据您提供的信息"这种机械的开头
"""

    try:
        from langchain_core.messages import HumanMessage
        response = llm.invoke([HumanMessage(content=prompt)])
        analysis = response.content if hasattr(response, "content") else str(response)
        logger.info(f"[report_agent] LLM 法律分析完成，长度: {len(analysis)} 字符")
        return analysis
    except Exception as e:
        logger.error(f"[report_agent] LLM 法律分析失败: {e}")
        return _fallback_analysis(user_input, emotion_type)


def _fallback_analysis(user_input: str, emotion_type: str = "neutral") -> str:
    """无 LLM 时的兜底分析（带情绪感知的通用模板）"""

    # 情绪回应
    emotion_responses = {
        "anxious": "我理解您现在很着急，请放心，这种情况是有明确的法律途径可以解决的。\n\n",
        "fearful": "请不必害怕，法律是保护劳动者的，您有充分的权利维护自己的合法权益。\n\n",
        "sad": "我能理解您现在的心情，遇到这样的事情确实令人难过。但请相信，法律会给您一个公正的结果。\n\n",
        "angry": "您的愤怒完全可以理解，遇到这种事情任谁都会气愤。让我们用法律的方式来解决这个问题。\n\n",
        "frustrated": "我知道您可能觉得很无助，但其实有很多成功的维权案例，只要走对步骤，您完全可以拿回属于自己的权益。\n\n",
        "confused": "别担心，我来帮您梳理一下思路，这种情况其实处理起来并不复杂。\n\n",
        "neutral": "",
    }
    emotion_prefix = emotion_responses.get(emotion_type, "")

    return (
        f"{emotion_prefix}"
        "### 法律判断\n"
        "根据您描述的情况，用人单位长期拖欠工资的行为**违反了劳动法相关规定**。"
        "《劳动法》第五十条明确规定：工资应当以货币形式按月支付给劳动者本人，不得克扣或者无故拖欠劳动者的工资。\n\n"
        "### 维权建议\n"
        "建议您按以下顺序采取行动：\n\n"
        "**第一步：收集证据。** 保存好劳动合同、工资条、考勤记录、银行流水、"
        "与公司沟通的聊天记录等能证明劳动关系和拖欠工资事实的材料。\n\n"
        "**第二步：协商解决。** 先尝试与用人单位沟通，要求支付拖欠的工资。"
        "协商时保留书面或录音证据。\n\n"
        "**第三步：劳动仲裁。** 协商不成，可在劳动关系终止之日起一年内，"
        "向当地劳动争议仲裁委员会申请劳动仲裁。注意不要超过时效。\n\n"
        "**第四步：寻求帮助。** 可拨打 **12333** 劳动保障热线，"
        "或向当地法律援助中心申请免费法律援助。也可以向劳动监察大队投诉举报。\n\n"
        "### 相关法条\n"
        "- 《劳动法》第五十条：工资应当按月支付，不得克扣或无故拖欠\n"
        "- 《劳动合同法》第三十条：用人单位应当及时足额支付劳动报酬\n"
        "- 《劳动合同法》第八十五条：未及时足额支付劳动报酬的，由劳动行政部门责令限期支付\n\n"
        "> ⚠️ 以上为通用法律建议，具体方案请咨询专业律师。"
    )


# ---------------------------------------------------------------------------
# Agent 调用入口
# ---------------------------------------------------------------------------


def generate_report(
    user_input: str,
    extracted_intent: dict[str, Any],
    task_results: list[dict[str, Any]],
    user_emotion: dict[str, Any] | None = None,
) -> str:
    """生成最终法律分析报告

    报告结构：
      1. 报告头部（标题+时间）
      2. 用户诉求
      3. 法律分析与建议（LLM 生成，含情绪回应 + 法律判断 + 维权建议）
      4. 报告尾部
    """
    logger.info(f"[report_agent] 开始生成报告，任务结果数: {len(task_results)}")

    # 步骤1: 生成头部
    header = _format_section("header", "法律智能分析报告", "")

    # 步骤2: 用户诉求
    intent_section = _format_section("body", "用户诉求", user_input)

    # 步骤3: 收集查询结果，调用 LLM 生成分析
    all_query_results: list[str] = []
    for result in task_results:
        task_type = result.get("task_type", "unknown")
        if task_type == "legal_query":
            query_result = result.get("query_result", "") or result.get("result", "")
            if query_result:
                all_query_results.append(query_result)
        elif task_type == "contract_review":
            # 合同审查结果也传给 LLM 分析
            clause = result.get("final_clause", "")
            if clause:
                all_query_results.append(f"合同审查结果：{clause}")

    analysis_section = ""
    if all_query_results:
        combined_results = "\n\n---\n\n".join(all_query_results)
        # 限制传入 LLM 的文本长度
        if len(combined_results) > 3000:
            combined_results = combined_results[:3000] + "\n\n...(内容过长已截断)"
        analysis_text = _llm_legal_analysis(user_input, combined_results, user_emotion)
        analysis_section = _format_section("body", "法律分析与建议", analysis_text)
    else:
        # 没有查询结果，仍用 LLM 或兜底模板给出建议
        analysis_text = _llm_legal_analysis(user_input, "暂无相关法律知识库查询结果", user_emotion)
        analysis_section = _format_section("body", "法律分析与建议", analysis_text)

    # 步骤4: 生成尾部
    footer = _format_section("footer", "报告结束", "")

    report = "\n".join([header, intent_section, analysis_section, footer])
    logger.info("[report_agent] 报告生成完成")

    return report
