"""工具注册中心 — 原始工具实现 + agent-as-tool 注册

两类内容：
  1. 原始工具实现（底层能力，不带 @tool，以 _ 开头）
  2. agent-as-tool 注册（@tool 包装器，调用各 agent 入口函数）

所有外部消费者（main_graph、planner 等）只从这里 import，
不直接 import 各 agent 文件。
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

import httpx
from langchain_core.tools import tool

logger = logging.getLogger(__name__)


# ===========================================================================
# 一、原始工具实现（底层能力）
# ===========================================================================


# ---------------------------------------------------------------------------
# 小理 AI 法律知识库
# ---------------------------------------------------------------------------

_XIAOLI_APPID: str = os.getenv("XIAOLI_APPID", "QthdBErlyaYvyXul")
_XIAOLI_SECRET: str = os.getenv("XIAOLI_SECRET", "EC5D455E6BD348CE8E18BE05926D2EBE")
_XIAOLI_BASE_URL: str = os.getenv(
    "XIAOLI_BASE_URL",
    "https://openapi.delilegal.com/api/qa/v3/search/queryListCase",
)
_XIAOLI_TIMEOUT: float = float(os.getenv("XIAOLI_TIMEOUT", "30"))


def _call_xiaoli_api(
    keywords: list[str],
    page_no: int = 1,
    page_size: int = 5,
    sort_field: str = "correlation",
    sort_order: str = "desc",
) -> dict[str, Any]:
    """调用小理 AI API（同步版本，含 SSL 错误重试）"""
    import time

    headers = {
        "appid": _XIAOLI_APPID,
        "secret": _XIAOLI_SECRET,
        "Content-Type": "application/json",
    }
    payload = {
        "pageNo": page_no,
        "pageSize": page_size,
        "sortField": sort_field,
        "sortOrder": sort_order,
        "condition": {"keywordArr": keywords},
    }
    logger.info(f"[xiaoli] API 请求: keywords={keywords}, page={page_no}, size={page_size}")
    logger.debug(f"[xiaoli] API payload: {json.dumps(payload, ensure_ascii=False)}")

    max_retries = 2
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            with httpx.Client(timeout=_XIAOLI_TIMEOUT) as client:
                response = client.post(_XIAOLI_BASE_URL, json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()

            total = result.get("body", {}).get("totalCount", 0)
            data_count = len(result.get("body", {}).get("data", []))
            logger.info(f"[xiaoli] API 响应: totalCount={total}, 返回条数={data_count}")
            logger.debug(f"[xiaoli] API 完整响应(前500字): {json.dumps(result, ensure_ascii=False)[:500]}")
            return result

        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            last_error = e
            if attempt < max_retries:
                wait = 2 ** attempt
                logger.warning(f"[xiaoli] API 请求失败(第{attempt + 1}次): {type(e).__name__} - {e}，{wait}秒后重试...")
                time.sleep(wait)
            else:
                logger.error(f"[xiaoli] API 请求失败(已重试{max_retries}次): {type(e).__name__} - {e}")

    raise last_error  # type: ignore[misc]


def _search_xiaoli(query: str, context: str = "") -> str:
    """搜索小理法律知识库，返回格式化文本

    内部会调用 keyword_extraction_agent 从用户输入中提取精准法律关键词，
    避免口语化噪音词导致 AND 逻辑搜索结果为空。

    Args:
        query: 搜索关键词或法律问题
        context: 案情背景（可选，会作为补充关键词）

    Returns:
        搜索结果文本
    """
    try:
        from agents.keyword_extraction_agent import extract_keywords

        logger.info(f"[xiaoli] _search_xiaoli 开始: query='{query}', context='{context[:100] if context else ''}'")

        keywords = extract_keywords(query)
        logger.info(f"[xiaoli] 关键词提取结果: {keywords}")

        if context:
            ctx_keywords = extract_keywords(context)
            # 去重：不重复添加已有关键词
            for kw in ctx_keywords:
                if kw not in keywords:
                    keywords.append(kw)
            logger.info(f"[xiaoli] 合并context后关键词: {keywords}")

        result = _call_xiaoli_api(keywords=keywords)
        body = result.get("body", {})
        total_count = body.get("totalCount", 0)
        data_list = body.get("data", [])

        if not data_list:
            logger.info(f"[xiaoli] 无搜索结果，keywords={keywords}")
            return "未检索到相关法律信息，请尝试调整查询关键词。"

        display_list = data_list[:2]  # 只取前2条，避免 LLM 上下文过长
        parts: list[str] = [
            f"共检索到 {total_count} 条相关结果，以下为前 {len(display_list)} 条：",
            "",
        ]

        for i, item in enumerate(display_list):
            title = item.get("title", "无标题")
            content = item.get("content", "")
            clean_title = re.sub(r"<[^>]+>", "", title)
            if len(clean_title) > 40:
                clean_title = clean_title[:40] + "..."
            clean_content = re.sub(r"<[^>]+>", "", content)
            if len(clean_content) > 150:
                clean_content = clean_content[:150] + "..."
            parts.append(f"### {i}. {clean_title}")
            parts.append(clean_content)
            parts.append("")

        result_text = "\n".join(parts)
        logger.info(f"[xiaoli] 格式化结果: {total_count}条, 文本长度={len(result_text)}")
        return result_text

    except httpx.HTTPStatusError as e:
        return f"知识库请求失败，HTTP {e.response.status_code}：{e.response.text[:200]}"
    except httpx.RequestError as e:
        return f"知识库网络异常：{type(e).__name__} - {e}"
    except Exception as e:
        return f"知识库调用出错：{type(e).__name__} - {e}"


# ---------------------------------------------------------------------------
# 文件读取
# ---------------------------------------------------------------------------


def _read_file(file_path: str) -> dict[str, Any]:
    """读取单个文件（PDF/DOCX/TXT），返回内容字典"""
    from agents.file_reader import read_file
    return read_file(file_path)


def _read_files(file_paths: list[str]) -> list[dict[str, Any]]:
    """批量读取多个文件"""
    from agents.file_reader import read_files
    return read_files(file_paths)


# ---------------------------------------------------------------------------
# 意图分类
# ---------------------------------------------------------------------------


def _classify_intent(user_input: str) -> dict[str, Any]:
    """意图分类的原始逻辑（关键词匹配）"""
    has_contract = any(kw in user_input for kw in ("合同", "条款", "协议", "合约", "交付"))
    has_labor = any(kw in user_input for kw in ("工伤", "劳动", "工资", "解雇", "裁员", "试用期", "加班", "社保"))
    has_ip = any(kw in user_input for kw in ("侵权", "商标", "专利", "著作权", "盗版", "抄袭", "知识产权", "商业秘密"))
    has_fraud = any(kw in user_input for kw in ("骗", "诈骗", "欺诈", "被骗", "骗局", "骗局", "假", "虚假"))
    has_consumer = any(kw in user_input for kw in ("退货", "退款", "假货", "质量", "赔偿", "维权", "投诉", "商家", "卖家", "买家", "发货"))
    has_legal = any(kw in user_input for kw in ("法规", "法律", "法条", "司法解释", "查询", "规定", "依据"))

    if has_ip:
        return {"intent": "ip_trade_secret", "domain": "ip", "confidence": 0.9,
                "reasoning": "用户输入涉及知识产权/商业秘密"}
    if has_contract:
        return {"intent": "contract_review", "domain": "contract", "confidence": 0.9,
                "reasoning": "用户输入涉及合同/条款相关内容"}
    if has_labor:
        return {"intent": "labor_dispute", "domain": "labor", "confidence": 0.85,
                "reasoning": "用户输入涉及劳动法相关问题"}
    if has_fraud or has_consumer:
        return {"intent": "fraud_consumer", "domain": "consumer", "confidence": 0.85,
                "reasoning": "用户输入涉及诈骗/消费纠纷/网购维权"}
    if has_legal:
        return {"intent": "legal_query", "domain": "general", "confidence": 0.7,
                "reasoning": "用户输入涉及法律法规查询"}

    return {"intent": "legal_consultation", "domain": "general", "confidence": 0.5,
            "reasoning": "未识别到明确的法律意图，作为通用咨询处理"}


# ---------------------------------------------------------------------------
# 事实核查
# ---------------------------------------------------------------------------


def _verify_fact(result_data: str, task_type: str) -> dict[str, Any]:
    """事实核查的原始逻辑"""
    try:
        result = json.loads(result_data) if isinstance(result_data, str) else result_data
    except json.JSONDecodeError:
        result = {"raw": result_data}

    issues: list[str] = []
    confidence = 0.8

    if task_type == "legal_query":
        query_result = result.get("query_result", "")
        if not query_result or len(query_result) < 20:
            issues.append("查询结果为空或过短，可能未检索到有效信息")
            confidence -= 0.3
        if "无" in query_result and "检索" in query_result:
            issues.append("检索结果为空，建议调整查询关键词重试")
            confidence -= 0.2

    elif task_type == "contract_review":
        final_clause = result.get("final_clause", "")
        review_rounds = result.get("review_rounds", 0)
        if not final_clause:
            issues.append("审查后条款为空，审查过程可能异常")
            confidence -= 0.4
        if review_rounds == 0:
            issues.append("审查轮次为0，红蓝对抗可能未正常执行")
            confidence -= 0.3

    confidence = max(confidence, 0.0)
    return {"is_accurate": len(issues) == 0, "issues": issues, "confidence": round(confidence, 2)}


def _check_consistency(result_data: str, user_input: str, task_type: str) -> dict[str, Any]:
    """逻辑一致性检查的原始逻辑"""
    try:
        result = json.loads(result_data) if isinstance(result_data, str) else result_data
    except json.JSONDecodeError:
        result = {"raw": result_data}

    issues: list[str] = []
    consistency_score = 0.8

    if task_type == "contract_review":
        clause = result.get("final_clause", "")
        if clause and user_input:
            input_keywords = set(user_input.replace("，", " ").replace("。", " ").split())
            clause_keywords = set(clause.replace("，", " ").replace("。", " ").split())
            overlap = input_keywords & clause_keywords
            if not overlap:
                issues.append("最终条款与用户原始条款无明显关联")
                consistency_score -= 0.3

    elif task_type == "legal_query":
        query_result = result.get("query_result", "")
        if query_result and user_input:
            legal_domains = ["合同", "劳动", "侵权", "公司", "知识产权", "刑法", "民法"]
            user_domain = [d for d in legal_domains if d in user_input]
            result_domain = [d for d in legal_domains if d in query_result]
            if user_domain and not result_domain:
                issues.append(f"用户关心 {user_domain} 领域，但查询结果未涉及")
                consistency_score -= 0.2

    consistency_score = max(consistency_score, 0.0)
    return {"is_consistent": len(issues) == 0, "issues": issues, "consistency_score": round(consistency_score, 2)}


# ---------------------------------------------------------------------------
# 报告格式化
# ---------------------------------------------------------------------------


def _format_section(section_type: str, title: str, content: str) -> str:
    """格式化报告段落"""
    from datetime import datetime
    if section_type == "header":
        return (
            "=" * 60 + "\n"
            + title + "\n"
            + f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            + "=" * 60
        )
    elif section_type == "footer":
        return "=" * 60 + "\n" + title + "\n" + "=" * 60
    else:
        return f"\n## {title}\n{content}\n"


def _summarize_result(task_type: str, task_description: str, result_data: str) -> str:
    """格式化单个任务结果"""
    lines = [f"## 任务：{task_description} [完成]"]
    if task_type == "contract_review":
        lines.append(result_data)
    elif task_type == "legal_query":
        lines.append(f"- 查询结果：\n{result_data}")
    else:
        lines.append(result_data)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 信息完整性分析
# ---------------------------------------------------------------------------


def _analyze_info_completeness(
    intent: str,
    user_input: str,
    conversation_history: list[dict[str, str]],
    legal_query_result: str,
) -> dict[str, Any]:
    """分析用户已提供的信息是否足够，输出缺少的信息项

    根据意图类型，确定法律要件清单，对比用户已提供的信息，
    判断哪些要件仍然缺失。

    Args:
        intent: 意图类型（ip_trade_secret / contract_review / labor_dispute 等）
        user_input: 用户原始输入
        conversation_history: 多轮对话历史
        legal_query_result: 之前查询法律知识库的结果

    Returns:
        {"info_complete": bool, "missing_info": [...], "pending_question": str}
    """
    # 根据意图类型确定法律要件
    REQUIRED_INFO = {
        "ip_trade_secret": [
            "商业秘密的具体内容",
            "保密措施",
            "泄密方式",
            "泄密造成的损失",
        ],
        "contract_review": [
            "合同条款原文",
            "合同类型",
            "关注的法律风险",
        ],
        "labor_dispute": [
            "劳动关系类型",
            "争议发生时间",
            "公司具体行为",
            "期望的补偿或诉求",
        ],
        "fraud_consumer": [
            "被骗/交易的具体经过",
            "涉及的金额",
            "对方的身份或联系方式",
            "已采取的措施",
        ],
    }

    default_requirements = ["案件的基本事实", "具体法律诉求"]
    requirements = REQUIRED_INFO.get(intent, default_requirements)

    # 合并用户所有已提供的信息
    all_user_text = user_input
    for msg in conversation_history:
        if msg.get("role") == "user":
            all_user_text += " " + msg.get("content", "")

    # 简单关键词匹配判断是否已提供
    KEYWORD_MAP = {
        "商业秘密的具体内容": ["技术", "配方", "工艺", "数据", "客户名单", "代码", "算法", "设计", "方案"],
        "保密措施": ["保密协议", "NDA", "限制访问", "密码", "权限", "加密", "保密制度", "保密条款"],
        "泄密方式": ["泄露", "窃取", "复制", "带走", "传播", "公开", "提供", "出售", "转移"],
        "泄密造成的损失": ["损失", "损害", "影响", "利润", "市场份额", "竞争优势"],
        "合同条款原文": ["条款", "约定", "甲方", "乙方", "合同", "协议"],
        "合同类型": ["买卖", "租赁", "租", "服务", "劳动", "合作", "投资", "采购", "租房"],
        "关注的法律风险": ["风险", "违约", "责任", "漏洞", "不利", "问题", "纠纷", "争议", "怎么处理", "如何处理", "怎么办"],
        "劳动关系类型": ["正式员工", "试用期", "劳务派遣", "兼职", "实习"],
        "争议发生时间": ["时间", "日期", "年", "月", "日", "最近", "上周", "昨天"],
        "公司具体行为": ["解雇", "辞退", "裁员", "降薪", "调岗", "拖欠", "不续签", "未支付"],
        "期望的补偿或诉求": ["补偿", "赔偿", "恢复", "继续", "要求", "想要", "申请"],
        "被骗/交易的具体经过": ["被骗", "骗", "诈骗", "购买", "交易", "付款", "转账", "发货", "网购", "线上", "线下"],
        "涉及的金额": ["元", "万", "块", "块钱", "金额", "费用", "价格", "损失", "2000", "房租"],
        "对方的身份或联系方式": ["卖家", "商家", "对方", "公司", "平台", "微信", "电话", "名字"],
        "已采取的措施": ["报警", "投诉", "联系", "协商", "举报", "起诉", "退款", "退货"],
        "案件的基本事实": ["发生", "经过", "因为", "导致", "造成"],
        "具体法律诉求": ["想要", "要求", "申请", "能否", "可以", "怎么办", "处理"],
    }

    missing: list[str] = []
    for req in requirements:
        keywords = KEYWORD_MAP.get(req, [])
        provided = any(kw in all_user_text for kw in keywords)
        if not provided:
            missing.append(req)

    info_complete = len(missing) == 0

    # 生成提问
    if missing:
        pending_question = f"为了更准确地为您分析，还需要了解以下信息：\n"
        for i, item in enumerate(missing, 1):
            pending_question += f"  {i}. {item}\n"
        pending_question += "请补充以上信息，以便我们提供更专业的法律分析。"
    else:
        pending_question = ""

    return {
        "info_complete": info_complete,
        "missing_info": missing,
        "pending_question": pending_question,
    }



# ===========================================================================
# 二、agent-as-tool 注册（@tool 包装器，只做调用转发）
# ===========================================================================


@tool
def use_legal_query(query: str, context: str = "") -> str:
    """查询法律知识库，获取相关法规和司法解释。

    适合以下场景：
    - 查找具体法条原文
    - 获取司法解释
    - 检索裁判规则和案例
    - 核实法律主张是否有依据

    Args:
        query: 法律查询问题
        context: 案情背景（可选）

    Returns:
        查询结果文本
    """
    from agents.legal_query_agent import query_legal
    return query_legal(query=query, context=context)


@tool
def use_contract_review(clause_text: str, legal_evidence: str = "[]") -> str:
    """对合同条款执行红蓝对抗审查。

    会经过多轮"红方攻击→蓝方防御→裁判评估"循环，
    直到条款通过审查或达到最大轮次。

    Args:
        clause_text: 需要审查的合同条款文本
        legal_evidence: 法律依据的 JSON 字符串（可选）

    Returns:
        审查结果 JSON 字符串
    """
    from agents.drafting_subgraph import drafting_subgraph

    evidence = []
    if legal_evidence and legal_evidence != "[]":
        try:
            evidence = json.loads(legal_evidence)
        except json.JSONDecodeError:
            pass

    sub_result = drafting_subgraph.invoke({
        "current_clause": clause_text,
        "legal_evidence": evidence,
        "draft_history": [],
        "is_approved": False,
    })

    result = {
        "is_approved": sub_result.get("is_approved", False),
        "final_clause": sub_result.get("current_clause", ""),
        "review_rounds": sum(
            1 for h in sub_result.get("draft_history", [])
            if h.get("role") == "judge"
        ),
    }
    return json.dumps(result, ensure_ascii=False)


@tool
def use_verifier(result_data: str, user_input: str, task_type: str) -> str:
    """校验任务结果的事实准确性和逻辑一致性。

    会对结果进行：
    1. 事实核查：法律引用是否真实
    2. 逻辑一致性：结果是否回答了用户问题
    3. 综合评估：质量打分

    Args:
        result_data: 任务结果的 JSON 字符串
        user_input: 用户原始输入
        task_type: 任务类型（contract_review / legal_query）

    Returns:
        校验结果 JSON 字符串
    """
    from agents.verifier_agent import verify_task_result

    try:
        task_result = json.loads(result_data) if isinstance(result_data, str) else result_data
    except (json.JSONDecodeError, TypeError):
        task_result = {"raw": result_data}

    verification = verify_task_result(
        task_result=task_result,
        user_input=user_input,
        retry_count=0,
    )
    return json.dumps(verification, ensure_ascii=False)


@tool
def use_file_reader(file_path: str) -> str:
    """读取文件内容（支持 PDF、DOCX、TXT、MD 格式）。

    适合以下场景：
    - 读取用户上传的合同文件
    - 提取法律文书内容
    - 读取案例资料

    Args:
        file_path: 文件路径

    Returns:
        文件内容 JSON 字符串，包含 filename、content、format 等
    """
    result = _read_file(file_path)
    return json.dumps(result, ensure_ascii=False)


@tool
def use_multi_file_reader(file_paths: str) -> str:
    """批量读取多个文件的内容。

    Args:
        file_paths: 文件路径列表的 JSON 字符串，如 '["a.pdf", "b.docx"]'

    Returns:
        所有文件内容的 JSON 字符串
    """
    try:
        paths = json.loads(file_paths) if isinstance(file_paths, str) else file_paths
    except json.JSONDecodeError:
        return json.dumps({"error": f"无法解析文件路径列表: {file_paths}"}, ensure_ascii=False)

    results = _read_files(paths)
    return json.dumps(results, ensure_ascii=False)


@tool
def use_report_generator(
    user_input: str,
    extracted_intent: str,
) -> str:
    """生成法律分析报告。

    Args:
        user_input: 用户原始输入
        extracted_intent: 意图分析结果的 JSON 字符串

    Returns:
        完整的法律分析报告文本
    """
    from agents.report_agent import generate_report

    try:
        intent = json.loads(extracted_intent) if isinstance(extracted_intent, str) else extracted_intent
    except json.JSONDecodeError:
        intent = {}

    # execution_results 从全局状态中获取，不需要 LLM 传递
    # LLM 只需要传递 user_input 和 extracted_intent
    return json.dumps({
        "status": "report_generated",
        "user_input": user_input,
        "extracted_intent": intent,
        "message": "报告生成参数已准备完毕，系统将自动补充执行结果并生成完整报告",
    }, ensure_ascii=False)


@tool
def analyze_info_completeness(
    intent: str,
    user_input: str,
    conversation_history: str = "[]",
    legal_query_result: str = "",
) -> str:
    """分析用户已提供的信息是否完整，判断是否需要追问。

    根据法律意图类型，列出该类案件需要的关键信息清单，
    对比用户已提供的内容，找出缺失项并生成追问问题。

    适合以下场景：
    - 判断用户描述的案件信息是否充分
    - 确定需要向用户追问哪些关键信息
    - 确保进入执行阶段前信息已周全

    Args:
        intent: 意图类型（ip_trade_secret / contract_review / labor_dispute 等）
        user_input: 用户原始输入
        conversation_history: 多轮对话历史的 JSON 字符串
        legal_query_result: 之前查询法律知识库的结果（用于辅助判断）

    Returns:
        信息完整性分析结果的 JSON 字符串
    """
    try:
        history = json.loads(conversation_history) if isinstance(conversation_history, str) else conversation_history
    except json.JSONDecodeError:
        history = []

    result = _analyze_info_completeness(
        intent=intent,
        user_input=user_input,
        conversation_history=history,
        legal_query_result=legal_query_result,
    )
    return json.dumps(result, ensure_ascii=False)


@tool
def analyze_emotion(user_input: str, conversation_history: str = "[]") -> str:
    """分析用户输入中的情绪状态。

    会识别用户的焦虑、愤怒、悲伤、困惑等情绪，并给出沟通建议。
    在意图分析阶段调用，帮助后续节点调整回复策略。

    Args:
        user_input: 用户的原始法律诉求文本
        conversation_history: 多轮对话历史的 JSON 字符串（可选）

    Returns:
        情绪分析结果的 JSON 字符串，包含 emotion、intensity、keywords、suggestion
    """
    from agents.emotion_agent import _analyze_emotion

    try:
        history = json.loads(conversation_history) if isinstance(conversation_history, str) else conversation_history
    except json.JSONDecodeError:
        history = []

    result = _analyze_emotion(user_input, history)
    return json.dumps(result, ensure_ascii=False)


@tool
def polish_report(report_content: str, user_emotion: str = "") -> str:
    """根据用户情绪状态润色法律分析报告。

    会读取情绪分析结果，调整报告的语气、开场白和结束语，
    使报告更贴合用户当前的心理状态。

    适合以下场景：
    - 报告生成后，作为最终润色步骤
    - 根据用户焦虑/愤怒/困惑等情绪调整措辞
    - 在开场和结尾添加情绪化的关怀语句

    Args:
        report_content: 原始报告文本
        user_emotion: 情绪分析结果的 JSON 字符串（可选）

    Returns:
        润色后的报告文本
    """
    from agents.polish_agent import _polish_report

    if not user_emotion:
        return report_content

    try:
        emotion = json.loads(user_emotion) if isinstance(user_emotion, str) else user_emotion
    except json.JSONDecodeError:
        emotion = {"emotion": "calm", "intensity": 0.0}

    return _polish_report(report_content, emotion)
