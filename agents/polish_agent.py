"""文本润色智能体 - 基于情绪信息润色最终报告

职责：
  - 读取 state 中的用户情绪分析结果
  - 根据情绪调整报告的语气和措辞
  - 对报告进行最终润色，使其更贴合用户情绪状态

润色策略：
  - anxious（焦虑）: 先安抚，再提供明确可行的行动建议
  - angry（愤怒）: 表示理解，强调维权途径和法律保障
  - sad（悲伤）: 语气温和，给予鼓励和支持
  - confused（困惑）: 结构清晰，用词通俗，分步骤说明
  - calm（平静）: 标准专业语气
"""

from __future__ import annotations

import logging
import re
from typing import Any

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 润色策略
# ---------------------------------------------------------------------------

EMOTION_POLISH_TEMPLATES: dict[str, dict[str, str]] = {
    "anxious": {
        "opening": "理解您的焦虑，以下是为您整理的法律分析，请放心，法律上有明确的应对措施：",
        "closing": "以上分析供您参考，建议尽快采取行动以维护您的合法权益。如有疑问，随时咨询。",
        "tone": "reassuring",
    },
    "angry": {
        "opening": "完全理解您的心情，法律为您提供了以下维权途径：",
        "closing": "您的合法权益受法律保护，建议通过合法途径坚决维权。我们随时为您提供支持。",
        "tone": "empathetic_firm",
    },
    "sad": {
        "opening": "非常理解您的处境，以下是我们为您准备的法律分析，希望能对您有所帮助：",
        "closing": "困难时刻请记住，法律是您最有力的后盾。祝您早日解决问题。",
        "tone": "gentle_supportive",
    },
    "confused": {
        "opening": "以下是为您梳理的法律分析，我们按步骤为您说明：",
        "closing": "如果您仍有疑问，建议就具体问题进一步咨询专业律师。",
        "tone": "clear_structured",
    },
    "calm": {
        "opening": "以下是法律分析报告：",
        "closing": "以上分析供您参考，如有进一步问题欢迎继续咨询。",
        "tone": "professional",
    },
}


def _polish_report(
    report_content: str,
    user_emotion: dict[str, Any],
) -> str:
    """根据情绪分析结果润色报告

    Args:
        report_content: 原始报告文本
        user_emotion: 情绪分析结果 dict，包含 emotion、intensity、keywords、suggestion

    Returns:
        润色后的报告文本
    """
    if not report_content:
        return report_content

    emotion = user_emotion.get("emotion", "calm") if user_emotion else "calm"
    intensity = user_emotion.get("intensity", 0.0) if user_emotion else 0.0

    # 获取润色模板
    template = EMOTION_POLISH_TEMPLATES.get(emotion, EMOTION_POLISH_TEMPLATES["calm"])

    # 如果情绪强度很低（< 0.2），使用标准语气
    if intensity < 0.2:
        template = EMOTION_POLISH_TEMPLATES["calm"]

    # 在报告头部和尾部插入情绪化措辞
    polished = report_content

    # 在第一个章节标题之前插入开场白
    header_match = re.search(r"={5,}", polished)
    if header_match:
        # 找到第一行 === 后面的标题行
        insert_pos = header_match.end()
        polished = polished[:insert_pos] + "\n" + template["opening"] + polished[insert_pos:]
    else:
        polished = template["opening"] + "\n\n" + polished

    # 在报告尾部添加结束语
    footer_match = re.search(r"={5,}\s*报告结束\s*={5,}", polished)
    if footer_match:
        polished = polished + "\n" + template["closing"]
    else:
        polished = polished + "\n\n" + template["closing"]

    # 针对特定情绪进行文本微调
    if emotion == "confused" and intensity >= 0.3:
        # 将连续的长段落拆分为分步骤
        polished = _add_step_markers(polished)

    logger.info(f"[polish_agent] 润色完成, 情绪={emotion}, 强度={intensity}, 语气={template['tone']}")
    return polished


def _add_step_markers(text: str) -> str:
    """对困惑用户添加步骤标记，使报告更清晰"""
    # 在"## 任务"段落中，为每个要点添加步骤编号
    lines = text.split("\n")
    result = []
    step = 0
    in_task_section = False

    for line in lines:
        if "## 任务" in line or "## 用户诉求" in line:
            in_task_section = True
        elif line.startswith("## ") and in_task_section:
            in_task_section = False

        if in_task_section and line.strip().startswith("- "):
            step += 1
            line = f"**步骤 {step}**: " + line.strip()[2:]

        result.append(line)

    return "\n".join(result)


# ---------------------------------------------------------------------------
# @tool 注册
# ---------------------------------------------------------------------------


@tool
def polish_report(report_content: str, user_emotion: str) -> str:
    """根据用户情绪状态润色法律分析报告。

    会读取情绪分析结果，调整报告的语气、开场白和结束语，
    使报告更贴合用户当前的心理状态。

    适合以下场景：
    - 报告生成后，作为最终润色步骤
    - 根据用户焦虑/愤怒/困惑等情绪调整措辞
    - 在开场和结尾添加情绪化的关怀语句

    Args:
        report_content: 原始报告文本
        user_emotion: 情绪分析结果的 JSON 字符串，
                      格式如 {"emotion": "anxious", "intensity": 0.7, "keywords": [...]}

    Returns:
        润色后的报告文本
    """
    import json
    try:
        emotion = json.loads(user_emotion) if isinstance(user_emotion, str) else user_emotion
    except json.JSONDecodeError:
        emotion = {"emotion": "calm", "intensity": 0.0}

    return _polish_report(report_content, emotion)
