"""情感分析智能体 - 分析用户输入中的情绪状态

职责：
  - 分析用户文本中的情绪类型（焦虑、愤怒、悲伤、平静等）
  - 评估情绪强度
  - 提取情绪关键词
  - 将分析结果写入 GlobalCaseState.user_emotion

策略：
  - 优先使用 LLM 进行语义级情绪分析（理解上下文、隐含情绪）
  - LLM 不可用时降级到关键词匹配（规则兜底）

在 orchestrator 节点内被调用，作为第一个工具执行，
后续的法律查询和信息完整性分析都会参考情绪分析结果。
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 情绪关键词映射（规则兜底用）
# ---------------------------------------------------------------------------

EMOTION_KEYWORDS: dict[str, list[str]] = {
    "anxious": [
        "担心", "害怕", "焦虑", "急迫", "着急", "忧虑", "不安", "恐惧",
        "尽快", "马上", "紧急", "会不会", "能否", "可不可以",
    ],
    "angry": [
        "愤怒", "气愤", "不公平", "无耻", "欺诈", "欺骗", "侵权",
        "违规", "违法", "投诉", "举报", "维权", "不可以接受",
        "骗", "被骗", "诈骗", "假", "骗子", "不发货", "不退款",
    ],
    "sad": [
        "失望", "伤心", "无助", "无奈", "绝望", "痛苦", "困扰",
        "没办法", "走投无路", "没办法了", "追不回", "要不回来",
    ],
    "confused": [
        "不懂", "不明白", "不知道", "困惑", "迷茫", "不了解",
        "不清楚", "该如何", "怎么办", "求助", "能要回来吗", "能不能",
    ],
    "calm": [],  # 无明显情绪关键词时默认为平静
}

# 情绪对应建议
SUGGESTIONS: dict[str, str] = {
    "anxious": "用户情绪焦虑，建议回复时先安抚情绪再提供法律建议",
    "angry": "用户情绪愤怒，建议回复时表示理解并强调维权途径",
    "sad": "用户情绪低落，建议回复时语气温和并给予支持",
    "confused": "用户情绪困惑，建议回复时结构清晰、用词通俗易懂",
    "calm": "用户情绪平和，可以直接提供法律分析",
}


# ---------------------------------------------------------------------------
# LLM 情绪分析 Prompt
# ---------------------------------------------------------------------------

_EMOTION_PROMPT = """你是一位专业的法律咨询情绪分析师。请根据用户的法律诉求文本，分析其情绪状态。

要求：
1. emotion：主导情绪类型，必须为以下之一：anxious（焦虑）、angry（愤怒）、sad（悲伤）、confused（困惑）、calm（平静）
2. intensity：情绪强度，范围 0.0-1.0（0.0=无情绪，1.0=极度强烈）
3. keywords：触发该情绪判断的关键词或短语列表（从原文中提取，最多5个）
4. reason：简要说明判断依据（一句话）
5. suggestion：给法律顾问的沟通建议

注意：
- 仔细体会用户文字背后的情绪，不要只看表面词义
- 例如"我被骗了十万块，一夜之间什么都没了"应判断为 sad+angry，而非仅 angry
- "我的商业秘密被前员工泄露了"这种客观陈述情绪可能较轻
- 涉及经济损失、人身威胁等重大事项时，即使用词平静也应考虑潜在焦虑

请严格以 JSON 格式输出，不要包含任何其他文字：
{{"emotion": "...", "intensity": 0.0, "keywords": ["..."], "reason": "...", "suggestion": "..."}}

用户法律诉求：
{user_text}"""


# ---------------------------------------------------------------------------
# LLM 驱动的情绪分析
# ---------------------------------------------------------------------------


def _analyze_emotion_with_llm(user_text: str) -> dict[str, Any] | None:
    """使用 LLM 分析用户情绪

    Args:
        user_text: 合并后的用户文本

    Returns:
        情绪分析结果字典，或 None（LLM 不可用/调用失败时）
    """
    from agents.llm_factory import get_llm

    llm = get_llm()
    if llm is None:
        logger.info("[emotion_agent] LLM 不可用，降级到关键词匹配")
        return None

    try:
        prompt = _EMOTION_PROMPT.format(user_text=user_text)
        logger.info(f"[emotion_agent] LLM 情绪分析请求，文本长度={len(user_text)}")

        response = llm.invoke(prompt)
        text = response.content.strip()
        logger.info(f"[emotion_agent] LLM 原始响应: {text[:200]}")

        # 从响应中提取 JSON（兼容 LLM 可能输出的 markdown 代码块）
        json_match = re.search(r'\{[^{}]+\}', text, re.DOTALL)
        if not json_match:
            logger.warning(f"[emotion_agent] LLM 响应中未找到 JSON，原文: {text[:100]}")
            return None

        result = json.loads(json_match.group())

        # 校验并规范化
        valid_emotions = {"anxious", "angry", "sad", "confused", "calm"}
        emotion = result.get("emotion", "calm")
        if emotion not in valid_emotions:
            logger.warning(f"[emotion_agent] LLM 返回未知情绪类型: {emotion}，降级到 calm")
            emotion = "calm"

        intensity = result.get("intensity", 0.5)
        try:
            intensity = float(intensity)
        except (ValueError, TypeError):
            intensity = 0.5
        intensity = max(0.0, min(1.0, round(intensity, 2)))

        keywords = result.get("keywords", [])
        if not isinstance(keywords, list):
            keywords = [str(keywords)]
        keywords = [str(kw) for kw in keywords[:5]]

        reason = result.get("reason", "")

        # 如果 LLM 没给 suggestion，根据情绪类型给出默认建议
        suggestion = result.get("suggestion", "") or SUGGESTIONS.get(emotion, "")

        return {
            "emotion": emotion,
            "intensity": intensity,
            "keywords": keywords,
            "reason": reason,
            "suggestion": suggestion,
        }

    except Exception as e:
        logger.warning(f"[emotion_agent] LLM 情绪分析失败: {e}", exc_info=True)
        return None


# ---------------------------------------------------------------------------
# 关键词匹配的情绪分析（规则兜底）
# ---------------------------------------------------------------------------


def _analyze_emotion_with_keywords(user_text: str) -> dict[str, Any]:
    """使用关键词匹配分析用户情绪（LLM 不可用时的兜底方案）

    Args:
        user_text: 合并后的用户文本

    Returns:
        情绪分析结果字典
    """
    emotion_scores: dict[str, float] = {}
    emotion_keywords_found: dict[str, list[str]] = {}

    for emotion, keywords in EMOTION_KEYWORDS.items():
        if emotion == "calm":
            continue
        found = [kw for kw in keywords if kw in user_text]
        if found:
            emotion_scores[emotion] = len(found) / max(len(keywords), 1)
            emotion_keywords_found[emotion] = found

    if not emotion_scores:
        return {
            "emotion": "calm",
            "intensity": 0.0,
            "keywords": [],
            "reason": "未匹配到任何情绪关键词",
            "suggestion": SUGGESTIONS["calm"],
        }

    primary_emotion = max(emotion_scores, key=lambda k: emotion_scores[k])
    intensity = min(emotion_scores[primary_emotion] * 3, 1.0)
    keywords = emotion_keywords_found[primary_emotion]

    return {
        "emotion": primary_emotion,
        "intensity": round(intensity, 2),
        "keywords": keywords,
        "reason": f"关键词匹配: {', '.join(keywords)}",
        "suggestion": SUGGESTIONS.get(primary_emotion, ""),
    }


# ---------------------------------------------------------------------------
# 统一入口
# ---------------------------------------------------------------------------


def _analyze_emotion(user_input: str, conversation_history: list[dict[str, str]] | None = None) -> dict[str, Any]:
    """分析用户输入中的情绪（优先 LLM，降级关键词）

    Args:
        user_input: 用户原始输入
        conversation_history: 多轮对话历史

    Returns:
        情绪分析结果，格式如：
        {
            "emotion": "anxious",
            "intensity": 0.7,
            "keywords": ["担心", "急迫"],
            "reason": "用户表达了对损失的担忧和急迫感",
            "suggestion": "用户情绪焦虑，建议回复时先安抚情绪再提供法律建议"
        }
    """
    # 合并所有用户输入
    all_text = user_input
    if conversation_history:
        for msg in conversation_history:
            if msg.get("role") == "user":
                all_text += " " + msg.get("content", "")

    # 优先使用 LLM
    result = _analyze_emotion_with_llm(all_text)

    # LLM 不可用或失败，降级到关键词匹配
    if result is None:
        result = _analyze_emotion_with_keywords(all_text)
        logger.info(f"[emotion_agent] 降级到关键词匹配: {result['emotion']} (强度: {result['intensity']})")
    else:
        logger.info(f"[emotion_agent] LLM 情绪分析: {result['emotion']} (强度: {result['intensity']})")

    return result


# ---------------------------------------------------------------------------
# @tool 注册
# ---------------------------------------------------------------------------


@tool
def analyze_emotion(user_input: str, conversation_history: str = "[]") -> str:
    """分析用户输入中的情绪状态。

    优先使用 LLM 进行语义级情绪分析，理解上下文和隐含情绪；
    LLM 不可用时自动降级到关键词匹配。
    在意图分析阶段调用，帮助后续节点调整回复策略。

    Args:
        user_input: 用户的原始法律诉求文本
        conversation_history: 多轮对话历史的 JSON 字符串（可选）

    Returns:
        情绪分析结果的 JSON 字符串，包含 emotion、intensity、keywords、reason、suggestion
    """
    try:
        history = json.loads(conversation_history) if isinstance(conversation_history, str) else conversation_history
    except json.JSONError:
        history = []

    result = _analyze_emotion(user_input, history)
    return json.dumps(result, ensure_ascii=False)
