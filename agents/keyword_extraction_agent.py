"""关键词提取智能体 — 将用户自然语言提炼为小理 API 搜索关键词

核心问题：
  小理 API 使用 AND 逻辑（所有关键词必须同时出现在结果中），
  口语化、噪音词会导致搜索结果为空。

策略：
  1. LLM 提取（优先）：用混元大模型从用户输入中提取法律领域核心关键词
  2. 规则兜底（fallback）：LLM 不可用时，用词表匹配 + 清洗规则

输出格式：
  空格分隔的精准关键词列表，如 "商业秘密 禁令 保密协议"
"""

from __future__ import annotations

import json
import logging
import re

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 法律领域核心词表（用于规则兜底和 LLM prompt 参考）
# ---------------------------------------------------------------------------

LEGAL_DOMAIN_TERMS: set[str] = {
    # 知识产权/商业秘密
    "商业秘密", "知识产权", "专利", "商标", "著作权", "侵权", "盗版",
    "保密协议", "保密措施", "禁令", "泄密", "NDA",
    "技术信息", "经营信息", "客户名单",
    # 合同
    "合同", "条款", "协议", "违约", "违约金", "解除", "撤销",
    "履行", "交付", "租赁", "买卖",
    # 劳动
    "劳动", "工伤", "工资", "解雇", "裁员", "社保", "加班",
    "试用期", "经济补偿", "违法解除",
    # 民法典/总则
    "民法典", "侵权责任", "损害赔偿", "精神损害", "连带责任",
    "诉讼时效", "善意取得", "无因管理", "不当得利",
    # 程序法
    "起诉", "仲裁", "调解", "上诉", "执行", "保全",
    "证据", "举证", "鉴定",
    # 其他高频法律词
    "赔偿", "责任", "权利", "义务", "法人", "股东",
    "欺诈", "胁迫", "重大误解", "显失公平",
    "构成要件", "法律依据", "司法解释",
}


# ---------------------------------------------------------------------------
# LLM 关键词提取
# ---------------------------------------------------------------------------

_EXTRACT_PROMPT = """你是一个法律搜索关键词提取专家。你的任务是从用户的法律问题中提取最适合法律数据库检索的关键词。

## 关键约束
- 搜索引擎使用 AND 逻辑：所有关键词必须同时出现在搜索结果中
- 因此关键词必须精准，不能包含口语化、情绪化或虚词
- 关键词数量控制在 2~5 个，宁少勿多
- 只保留法律领域术语和案件核心要素词

## 提取原则
1. 优先提取法律专业术语（如"商业秘密""侵权责任""违约金"）
2. 保留案件关键实体（如"劳动合同""股权""房产"）
3. 去掉疑问词（吗、呢、吧、怎么、如何、能不能）
4. 去掉口语化表达（被、能、想、要、应该、可以、的、了、着、过）
5. 去掉模糊量词和程度词（很多、非常、严重、一些）

## 输出格式
只输出关键词，用空格分隔，不要任何解释。
例如：商业秘密 禁令 保密协议

## 用户问题
{query}"""


def _extract_keywords_with_llm(raw_query: str) -> list[str] | None:
    """用 LLM 提取搜索关键词

    Args:
        raw_query: 用户原始问题

    Returns:
        提取的关键词列表，如 LLM 不可用则返回 None
    """
    from agents.llm_factory import get_llm

    llm = get_llm()
    if llm is None:
        logger.info("[keyword_agent] LLM 不可用，将使用规则兜底")
        return None

    try:
        prompt = _EXTRACT_PROMPT.format(query=raw_query)
        logger.info(f"[keyword_agent] LLM 请求 prompt:\n{prompt}")
        logger.info(f"[keyword_agent] LLM 请求原文: '{raw_query}'")

        response = llm.invoke(prompt)
        text = response.content.strip()
        logger.info(f"[keyword_agent] LLM 原始响应: '{text}'")

        # 解析 LLM 输出：空格分隔的关键词
        keywords = [kw.strip() for kw in text.split() if kw.strip()]

        if not keywords:
            logger.warning(f"[keyword_agent] LLM 返回空关键词，原文: {raw_query[:50]}")
            return None

        # 过滤过短或明显非关键词的结果
        keywords = [kw for kw in keywords if len(kw) >= 2]

        logger.info(f"[keyword_agent] LLM 提取结果: '{raw_query}' → {keywords}")
        return keywords

    except Exception as e:
        logger.warning(f"[keyword_agent] LLM 提取失败: {e}", exc_info=True)
        return None


# ---------------------------------------------------------------------------
# 规则兜底：词表匹配 + 清洗
# ---------------------------------------------------------------------------


def _extract_keywords_with_rules(raw_query: str) -> list[str]:
    """用规则词表匹配提取关键词（LLM 不可用时的兜底）

    策略：
      1. 优先从输入中匹配法律领域词表中的词（长词优先）
      2. 如未匹配到任何领域词，则清洗后整体作为查询

    Args:
        raw_query: 用户原始问题

    Returns:
        提取的关键词列表
    """
    # 第一步：优先匹配法律领域实体词（长词优先，避免子串误匹配）
    matched_terms: list[str] = []
    remaining = raw_query
    for term in sorted(LEGAL_DOMAIN_TERMS, key=len, reverse=True):
        if term in remaining:
            matched_terms.append(term)
            remaining = remaining.replace(term, " ", 1)

    # 如果匹配到了法律领域词，直接使用
    if matched_terms:
        logger.info(f"[keyword_agent] 规则提取(词表匹配): '{raw_query}' → {matched_terms}")
        return matched_terms

    # 第二步：未匹配到领域词时的兜底 — 清洗后整体作为查询
    fallback = re.sub(r"[吗呢吧啊呀？！，。、；：""''（）【】]+", " ", raw_query).strip()
    fallback = re.sub(r"\s+", " ", fallback)

    result = fallback.split() if fallback else [raw_query]
    logger.info(f"[keyword_agent] 规则提取(清洗兜底): '{raw_query}' → {result}")
    return result


# ---------------------------------------------------------------------------
# 统一入口
# ---------------------------------------------------------------------------


def extract_keywords(raw_query: str) -> list[str]:
    """从用户自然语言中提取法律搜索关键词

    优先使用 LLM 提取，LLM 不可用时回退到规则词表匹配。

    Args:
        raw_query: 用户原始问题，如 "商业秘密被泄露，能申请禁令吗"

    Returns:
        关键词列表，如 ["商业秘密", "禁令"]
    """
    if not raw_query or not raw_query.strip():
        logger.info("[keyword_agent] 输入为空，返回空关键词列表")
        return []

    logger.info(f"[keyword_agent] ===== 开始提取关键词 =====")
    logger.info(f"[keyword_agent] 输入: '{raw_query}'")

    # 优先 LLM
    keywords = _extract_keywords_with_llm(raw_query)
    if keywords:
        logger.info(f"[keyword_agent] 最终结果(LLM): {keywords}")
        return keywords

    # 兜底规则
    result = _extract_keywords_with_rules(raw_query)
    logger.info(f"[keyword_agent] 最终结果(规则): {result}")
    return result
