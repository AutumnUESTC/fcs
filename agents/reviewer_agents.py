"""红蓝对抗审查智能体 - 红方攻击、蓝方防御、裁判判定

每个 Agent 设计为 ReAct 模式：
  - 红方: find_clause_vulnerabilities → generate_attack_opinion
  - 蓝方: analyze_attack → revise_clause → generate_defense_opinion
  - 裁判: count_review_rounds → evaluate_clause_quality

当前 mock 模式：函数内部按 ReAct 流程依次调用工具。
后续接入真实 LLM：替换为 create_react_agent。
"""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_core.tools import tool

from agents.states import DraftingSubState

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 红方攻击 Agent 的工具
# ---------------------------------------------------------------------------


@tool
def find_clause_vulnerabilities(clause: str, evidence_count: int) -> str:
    """分析合同条款，找出法律漏洞和风险点。"""
    vulnerabilities = [
        "1. 违约责任界定不清晰，缺乏量化标准",
        "2. 未明确争议解决的具体管辖机构",
        f"3. 现有法律依据 {evidence_count} 条，不足以覆盖全部风险场景",
    ]
    return "\n".join(vulnerabilities)


@tool
def generate_attack_opinion(clause: str, vulnerabilities: str) -> str:
    """根据发现的漏洞，生成红方攻击意见。"""
    clause_preview = clause[:50] + ("..." if len(clause) > 50 else "")
    return f"[红方攻击] 条款「{clause_preview}」存在以下风险：\n  {vulnerabilities}"


# ---------------------------------------------------------------------------
# 蓝方防御 Agent 的工具
# ---------------------------------------------------------------------------


@tool
def analyze_attack(attack_opinion: str) -> str:
    """分析红方攻击意见，提取需要回应的关键点。"""
    return f"需要回应的关键攻击点：{attack_opinion[:200]}"


@tool
def revise_clause(clause: str, attack_points: str) -> str:
    """根据攻击点修订合同条款。"""
    return (
        f"{clause}\n"
        f"（修订：明确违约金比例为合同总额的 5%-20%，"
        f"约定争议由合同签订地人民法院管辖，"
        f"补充引用《民法典》第 577 条作为法律依据。）"
    )


@tool
def generate_defense_opinion(attack_points: str, revised_clause: str) -> str:
    """生成蓝方防御意见。"""
    return (
        "[蓝方防御] 针对红方攻击进行如下修订：\n"
        "  1. 已补充违约金量化区间（5%-20%）\n"
        "  2. 已明确争议管辖机构\n"
        "  3. 已补充《民法典》第 577 条作为法律依据"
    )


# ---------------------------------------------------------------------------
# 裁判 Agent 的工具
# ---------------------------------------------------------------------------


@tool
def count_review_rounds(history_summary: str) -> str:
    """计算当前已完成几轮红蓝对抗。"""
    round_count = history_summary.count("红方攻击") if history_summary else 0
    return json.dumps({"rounds": max(round_count, 1)})


@tool
def evaluate_clause_quality(clause: str, round_info: str) -> str:
    """评估条款质量，决定是否通过审查。"""
    round_data = json.loads(round_info) if isinstance(round_info, str) else round_info
    rounds = round_data.get("rounds", 1)
    approved = rounds >= 3
    if approved:
        opinion = f"[裁判] 经过 {rounds} 轮红蓝对抗，条款风险已充分覆盖，法律依据充分。审查通过。"
    else:
        opinion = f"[裁判] 第 {rounds} 轮对抗完成，条款仍存在待完善之处，请蓝方继续修订。"
    return json.dumps({"is_approved": approved, "judge_opinion": opinion}, ensure_ascii=False)


# ---------------------------------------------------------------------------
# 节点函数（供 drafting_subgraph.py 的图使用）
# ---------------------------------------------------------------------------


def red_attacker(state: DraftingSubState) -> dict:
    """红方攻击节点"""
    clause = state.get("current_clause", "")
    evidence = state.get("legal_evidence", [])
    logger.info(f"[red_attacker] Agent 开始攻击: {clause[:50]}...")

    vulnerabilities = find_clause_vulnerabilities.invoke({"clause": clause, "evidence_count": len(evidence)})
    attack_opinion = generate_attack_opinion.invoke({"clause": clause, "vulnerabilities": vulnerabilities})

    logger.info("[red_attacker] 攻击完成")
    return {"draft_history": [{"role": "red_attacker", "content": attack_opinion}]}


def blue_defender(state: DraftingSubState) -> dict:
    """蓝方防御节点"""
    clause = state.get("current_clause", "")
    history = state.get("draft_history", [])

    latest_attack = ""
    for record in reversed(history):
        if record.get("role") == "red_attacker":
            latest_attack = record.get("content", "")
            break

    logger.info("[blue_defender] Agent 开始防御")

    attack_points = analyze_attack.invoke({"attack_opinion": latest_attack})
    revised_clause = revise_clause.invoke({"clause": clause, "attack_points": attack_points})
    defense_opinion = generate_defense_opinion.invoke({"attack_points": attack_points, "revised_clause": revised_clause})

    logger.info("[blue_defender] 防御完成")
    return {
        "current_clause": revised_clause,
        "draft_history": [{"role": "blue_defender", "content": defense_opinion, "revised_clause": revised_clause}],
    }


def judge(state: DraftingSubState) -> dict:
    """裁判节点"""
    history = state.get("draft_history", [])
    clause = state.get("current_clause", "")

    iteration_count = sum(1 for h in history if h.get("role") in ("red_attacker", "blue_defender")) // 2
    logger.info(f"[judge] Agent 开始评估，当前约第 {iteration_count} 轮")

    history_summary = "\n".join(f"{h.get('role')}: {h.get('content', '')[:100]}" for h in history)
    round_info = count_review_rounds.invoke({"history_summary": history_summary})
    eval_result_str = evaluate_clause_quality.invoke({"clause": clause, "round_info": round_info})

    eval_data = json.loads(eval_result_str)
    approved = eval_data.get("is_approved", iteration_count >= 3)
    judge_opinion = eval_data.get("judge_opinion", f"[裁判] 第 {iteration_count} 轮对抗完成，{'审查通过' if approved else '条款仍需完善'}。")

    logger.info(f"[judge] 评估完成: {'通过' if approved else '未通过'}")
    return {
        "is_approved": approved,
        "draft_history": [{"role": "judge", "content": judge_opinion, "approved": approved}],
    }
