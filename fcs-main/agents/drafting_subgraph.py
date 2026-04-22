"""合同审查子图 - 红蓝对抗审查 (Red-Blue Adversarial Review)

图结构：
  red_attacker → blue_defender → judge ──(未通过)──→ blue_defender (循环)
                                     └─(通过)────→ END

本文件只负责图的构建（节点、边、条件边），Agent 的具体实现从 reviewer_agents import。
"""

from __future__ import annotations

import logging

from langgraph.graph import END, StateGraph

from agents.reviewer_agents import red_attacker, blue_defender, judge
from agents.states import DraftingSubState

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 条件边函数
# ---------------------------------------------------------------------------


def should_continue(state: DraftingSubState) -> str:
    """裁判是否通过？"""
    if state.get("is_approved", False):
        return END
    return "blue_defender"


# ---------------------------------------------------------------------------
# 子图构建
# ---------------------------------------------------------------------------


def build_drafting_subgraph() -> StateGraph:
    """构建红蓝对抗审查子图"""
    builder = StateGraph(DraftingSubState)

    builder.add_node("red_attacker", red_attacker)
    builder.add_node("blue_defender", blue_defender)
    builder.add_node("judge", judge)

    builder.set_entry_point("red_attacker")

    builder.add_edge("red_attacker", "blue_defender")
    builder.add_edge("blue_defender", "judge")
    builder.add_conditional_edges(
        "judge",
        should_continue,
        {"blue_defender": "blue_defender", END: END},
    )

    return builder.compile()


# 模块级编译实例，供主工作流直接引用
drafting_subgraph = build_drafting_subgraph()


# ---------------------------------------------------------------------------
# 本地测试
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")

    initial_state: DraftingSubState = {
        "current_clause": "甲方应在合同签订后 30 日内交付产品，如逾期需承担违约责任。",
        "legal_evidence": [
            {"source": "《民法典》第 577 条", "content": "当事人一方不履行合同义务或者履行合同义务不符合约定的，应当承担继续履行、采取补救措施或者赔偿损失等违约责任。"},
            {"source": "《民法典》第 585 条", "content": "当事人可以约定一方违约时应当根据违约情况向对方支付一定数额的违约金。"},
        ],
        "draft_history": [],
        "is_approved": False,
    }

    result = drafting_subgraph.invoke(initial_state)
    print(f"\n审查结果: {'✅ 通过' if result['is_approved'] else '❌ 未通过'}")
    print(f"\n最终条款:\n{result['current_clause']}")
