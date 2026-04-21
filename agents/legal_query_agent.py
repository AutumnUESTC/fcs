"""法规查询智能体 - 调用法律知识库查询相关法规

ReAct 模式：
  步骤1: refine_search_keywords → 提炼搜索关键词
  步骤2: search_legal_database → 搜索法规（调用 tools.py 的 _search_xiaoli）
  步骤3: validate_query_result → 校验结果质量

当前 mock 模式：函数内部依次调用工具。
后续接入真实 LLM：替换为 create_react_agent。
"""

from __future__ import annotations

import json
import logging
import re

from langchain_core.tools import tool

from agents.tools import _search_xiaoli

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Agent 可调用的工具
# ---------------------------------------------------------------------------


@tool
def refine_search_keywords(raw_query: str) -> str:
    """将用户的自然语言问题提炼为精准的搜索关键词。

    调用 keyword_extraction_agent 提取法律领域核心关键词，
    支持 LLM 智能提取 + 规则词表兜底。
    小理 API 是 AND 逻辑（所有关键词必须同时出现），因此只保留
    精准的法律领域术语，避免噪音词导致搜索结果为空。

    Args:
        raw_query: 用户的原始问题

    Returns:
        提炼后的关键词（空格分隔）
    """
    from agents.keyword_extraction_agent import extract_keywords

    keywords = extract_keywords(raw_query)
    result = " ".join(keywords)
    logger.info(f"[legal_query_agent] refine_search_keywords: input='{raw_query}' -> output='{result}'")
    return result


@tool
def search_legal_database(query: str, context: str = "") -> str:
    """在法律知识库中搜索相关法规和案例。

    调用小理 AI 知识库进行检索。

    Args:
        query: 搜索关键词或法律问题
        context: 案情背景（可选）

    Returns:
        搜索结果文本
    """
    logger.info(f"[legal_query_agent] search_legal_database: query='{query}', context='{context[:50] if context else ''}'")
    result = _search_xiaoli(query=query, context=context)
    logger.info(f"[legal_query_agent] search_legal_database 结果长度: {len(result)}")
    return result


@tool
def validate_query_result(query: str, result: str) -> str:
    """校验查询结果的基本质量：非空、与查询相关。

    Args:
        query: 原始查询关键词
        result: search_legal_database 返回的结果

    Returns:
        校验结果 JSON 字符串
    """
    issues: list[str] = []

    if not result or len(result.strip()) < 10:
        issues.append("查询结果为空或过短")

    # 放宽关键词匹配：用法律领域词表提取查询中的核心词，再检查是否出现在结果中
    if query and result:
        from agents.keyword_extraction_agent import LEGAL_DOMAIN_TERMS, extract_keywords

        # 从原始查询中提取法律领域词
        matched_terms = [t for t in extract_keywords(query) if t in LEGAL_DOMAIN_TERMS]
        logger.info(f"[legal_query_agent] validate_query_result: query='{query}', matched_terms={matched_terms}")

        # 如果提取到领域词，检查是否出现在结果中
        if matched_terms:
            hit = sum(1 for t in matched_terms if t in result)
            logger.info(f"[legal_query_agent] validate_query_result: 关键词命中 {hit}/{len(matched_terms)}")
            if hit == 0:
                issues.append("查询结果与查询关键词无明显关联")
        else:
            # 未提取到领域词，回退到简单分词检查
            simple_tokens = set(re.sub(r"[，。？！、；：\s]+", " ", query).split())
            simple_tokens = {w for w in simple_tokens if len(w) >= 2}
            hit = sum(1 for w in simple_tokens if w in result)
            if simple_tokens and hit == 0:
                issues.append("查询结果与查询关键词无明显关联")

    # 注意：不再强制要求法律引用格式（《 或 第），
    # 因为知识库返回的内容格式多样，不应因缺少引用格式就拒绝结果

    is_valid = len(issues) == 0
    validation_result = {"is_valid": is_valid, "issues": issues}
    logger.info(f"[legal_query_agent] validate_query_result: {validation_result}")
    return json.dumps(validation_result, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Agent 调用入口
# ---------------------------------------------------------------------------


def query_legal(query: str, context: str = "") -> str:
    """使用 Agent 查询法律知识库

    ReAct 流程：
      思考1: "我需要提炼搜索关键词" → 调用 refine_search_keywords
      思考2: "关键词提炼完成，搜索法规" → 调用 search_legal_database
      思考3: "搜索完成，校验结果质量" → 调用 validate_query_result

    Args:
        query: 法律查询问题
        context: 案情背景（可选）

    Returns:
        查询结果文本（如校验发现问题，会附加警告标注）
    """
    logger.info(f"[legal_query_agent] ===== Agent 开始查询 =====")
    logger.info(f"[legal_query_agent] 输入: query='{query[:100]}', context='{context[:50] if context else ''}'")

    # 步骤1: 调用 refine_search_keywords
    logger.info("[legal_query_agent] 步骤1: 提炼搜索关键词")
    refined_query = refine_search_keywords.invoke({"raw_query": query})
    logger.info(f"[legal_query_agent] 步骤1结果: '{refined_query}'")

    # 步骤2: 调用 search_legal_database
    logger.info(f"[legal_query_agent] 步骤2: 搜索法规, 关键词='{refined_query}'")
    result = search_legal_database.invoke({"query": refined_query, "context": context})
    logger.info(f"[legal_query_agent] 步骤2结果: 长度={len(result)}, 前100字='{result[:100]}'")

    # 步骤3: 调用 validate_query_result 校验结果
    logger.info("[legal_query_agent] 步骤3: 校验结果质量")
    validation_str = validate_query_result.invoke({"query": query, "result": result})
    validation = json.loads(validation_str)
    logger.info(f"[legal_query_agent] 步骤3结果: {validation}")

    if not validation.get("is_valid", True):
        issues = validation.get("issues", [])
        logger.warning(
            f"[legal_query_agent] 查询结果校验未通过: {'; '.join(issues)}"
        )
        result += f"\n\n⚠️ [校验警告] 查询结果可能存在问题：{'；'.join(issues)}"
    else:
        logger.info("[legal_query_agent] 查询结果校验通过")

    logger.info("[legal_query_agent] 查询完成")

    return result
