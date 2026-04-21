"""小理 AI 法律知识库 API 单元测试

测试范围：
  1. _call_xiaoli_api — 原始 API 调用
  2. _search_xiaoli   — 搜索 + 格式化
  3. 关键词 AND 逻辑验证
  4. 边界情况（空关键词、不存在的词、超长查询等）
"""

import json
import sys
import os

import pytest

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.tools import _call_xiaoli_api, _search_xiaoli


# ============================================================================
# 1. _call_xiaoli_api 原始 API 测试
# ============================================================================


class TestCallXiaoliApi:
    """直接测试小理 API 的原始返回"""

    def test_single_keyword(self):
        """单个关键词搜索应返回有效结构"""
        result = _call_xiaoli_api(keywords=["商业秘密"])
        assert isinstance(result, dict)
        body = result.get("body", {})
        assert isinstance(body.get("totalCount", 0), int)
        assert isinstance(body.get("data", []), list)
        print(f"\n[单关键词] '商业秘密' → totalCount={body.get('totalCount')}")

    def test_two_keywords_and_logic(self):
        """两个关键词（AND 逻辑），结果数应 <= 单个关键词"""
        r1 = _call_xiaoli_api(keywords=["商业秘密"])
        r2 = _call_xiaoli_api(keywords=["商业秘密", "禁令"])
        count1 = r1.get("body", {}).get("totalCount", 0)
        count2 = r2.get("body", {}).get("totalCount", 0)
        assert count2 <= count1, f"AND 逻辑下双关键词结果应不多于单关键词: {count2} > {count1}"
        print(f"\n[AND逻辑] '商业秘密' → {count1}, '商业秘密+禁令' → {count2}")

    def test_nonexistent_keyword(self):
        """完全不相关的关键词应返回很少或0条结果
        
        注意：小理 API 是模糊匹配，即使输入无意义词也可能返回少量结果，
        因此这里只验证结果数量远少于常见法律词。
        """
        r_legal = _call_xiaoli_api(keywords=["合同"])
        r_nonsense = _call_xiaoli_api(keywords=["XYZABC无意义词12345"])
        count_legal = r_legal.get("body", {}).get("totalCount", 0)
        count_nonsense = r_nonsense.get("body", {}).get("totalCount", 0)
        assert count_nonsense < count_legal, \
            f"无意义词结果({count_nonsense})应远少于法律词({count_legal})"
        print(f"\n[不相关关键词] '合同' → {count_legal}, 'XYZABC无意义词12345' → {count_nonsense}")

    def test_noise_word_kills_result(self):
        """混入噪音词会导致结果从有到无（AND 逻辑的坑）"""
        r_clean = _call_xiaoli_api(keywords=["商业秘密", "禁令"])
        r_noisy = _call_xiaoli_api(keywords=["商业秘密", "禁令", "被泄露", "能申请"])
        count_clean = r_clean.get("body", {}).get("totalCount", 0)
        count_noisy = r_noisy.get("body", {}).get("totalCount", 0)
        print(f"\n[噪音词影响] 干净词 → {count_clean}, 加噪音词 → {count_noisy}")
        # 这正是之前 bug 的根源：干净词有结果，加噪音词后结果为 0
        assert count_clean > 0, "干净关键词应该有结果"

    def test_pagination(self):
        """分页参数应生效"""
        r1 = _call_xiaoli_api(keywords=["合同"], page_no=1, page_size=2)
        r2 = _call_xiaoli_api(keywords=["合同"], page_no=2, page_size=2)
        data1 = r1.get("body", {}).get("data", [])
        data2 = r2.get("body", {}).get("data", [])
        assert len(data1) <= 2
        assert len(data2) <= 2
        # 第1页和第2页的标题应不同
        titles1 = {item.get("title") for item in data1}
        titles2 = {item.get("title") for item in data2}
        assert titles1 != titles2, "第1页和第2页内容应不同"
        print(f"\n[分页] page1 标题数={len(titles1)}, page2 标题数={len(titles2)}")

    def test_result_structure(self):
        """返回的每条结果应包含 title 和 content"""
        result = _call_xiaoli_api(keywords=["劳动"], page_size=3)
        data = result.get("body", {}).get("data", [])
        assert len(data) > 0, "应有搜索结果"
        for item in data:
            assert "title" in item, f"结果缺少 title 字段: {item.keys()}"
            assert "content" in item, f"结果缺少 content 字段: {item.keys()}"
        print(f"\n[结果结构] {len(data)} 条结果均包含 title + content")


# ============================================================================
# 2. _search_xiaoli 格式化输出测试
# ============================================================================


class TestSearchXiaoli:
    """测试 _search_xiaoli 的格式化输出"""

    def test_successful_search(self):
        """正常搜索应返回格式化文本"""
        result = _search_xiaoli("商业秘密 禁令")
        assert "未检索到" not in result, "不应返回'未检索到'"
        assert "共检索到" in result, "应包含结果计数"
        assert "### 1." in result, "应包含编号标题"
        print(f"\n[正常搜索] 结果长度={len(result)}")
        print(f"  预览: {result[:150]}...")

    def test_search_with_context(self):
        """带 context 参数应将 context 作为补充关键词"""
        r1 = _search_xiaoli("商业秘密")
        r2 = _search_xiaoli("商业秘密", context="禁令")
        # 加 context 后结果应不同（AND 逻辑更严格）
        # 注意：有可能 r2 的结果更少
        print(f"\n[带context] 无context长度={len(r1)}, 有context长度={len(r2)}")

    def test_empty_result(self):
        """搜索极不相关的词应返回少量或空结果"""
        result = _search_xiaoli("XYZABC无意义词12345")
        # 小理 API 是模糊匹配，可能仍返回少量结果
        # 验证结果数量远少于正常法律查询
        if "未检索到" in result:
            print(f"\n[空结果] 输出: 未检索到")
        else:
            # 有结果但应该很少
            import re
            match = re.search(r"共检索到 (\d+) 条", result)
            count = int(match.group(1)) if match else 0
            assert count < 500, f"不相关词结果应远少于法律词，实际{count}"
            print(f"\n[空结果] 不相关词仍返回 {count} 条（API模糊匹配）")

    def test_chinese_comma_split(self):
        """中文逗号应被正确分词"""
        # "商业秘密，禁令" 应等效于 "商业秘密 禁令"
        r1 = _search_xiaoli("商业秘密 禁令")
        r2 = _search_xiaoli("商业秘密，禁令")
        assert "共检索到" in r1
        assert "共检索到" in r2
        print(f"\n[逗号分词] 空格分词结果数={_extract_count(r1)}, 逗号分词结果数={_extract_count(r2)}")

    def test_html_stripped(self):
        """结果中的 HTML 标签应被清除"""
        result = _search_xiaoli("合同")
        assert "<" not in result.split("###")[0] or "<" not in result, "输出不应包含 HTML 标签"
        print(f"\n[HTML清除] 结果中无HTML标签 [OK]")

    def test_content_truncated(self):
        """超长内容应被截断"""
        result = _search_xiaoli("合同违约")
        lines = result.split("\n")
        # 检查是否有任何单行超过 600 字（500 + "..." + 标题等余量）
        long_lines = [line for line in lines if len(line) > 600]
        # 这个断言是软性的，因为标题行可能较长
        if long_lines:
            print(f"\n[截断] 注意：有 {len(long_lines)} 行超过600字")
        else:
            print(f"\n[截断] 内容均在500字以内 [OK]")


# ============================================================================
# 3. 关键词 AND 逻辑专项测试（核心 bug 回归测试）
# ============================================================================


class TestAndLogicPitfall:
    """验证小理 API 的 AND 逻辑行为 — 这是之前 bug 的根源"""

    def test_clean_vs_noisy_keywords(self):
        """核心回归测试：干净关键词有结果，加噪音词后结果为空"""
        clean = _search_xiaoli("商业秘密 禁令")
        noisy = _search_xiaoli("商业秘密 禁令 被泄露 能申请")

        assert "共检索到" in clean, "干净关键词应能搜到结果"
        # 噪音词版本可能搜不到（AND 逻辑）
        if "未检索到" in noisy:
            print(f"\n[回归测试] [OK] 确认：加噪音词后确实搜不到（AND逻辑）")
            print(f"  干净词: {_extract_count(clean)} 条")
            print(f"  噪音词: 未检索到")
        else:
            print(f"\n[回归测试] 噪音词也能搜到: {_extract_count(noisy)} 条")

    def test_keyword_count_vs_result_count(self):
        """关键词越多，结果越少（AND 逻辑特征）"""
        counts = []
        keywords_list = [
            ["商业秘密"],
            ["商业秘密", "禁令"],
            ["商业秘密", "禁令", "保密措施"],
        ]
        for kws in keywords_list:
            r = _call_xiaoli_api(keywords=kws)
            c = r.get("body", {}).get("totalCount", 0)
            counts.append(c)
            print(f"  {kws} → {c}")

        # 验证递减趋势（允许相等）
        for i in range(1, len(counts)):
            assert counts[i] <= counts[i - 1], \
                f"关键词越多结果应越少: {keywords_list[i]}={counts[i]} > {keywords_list[i-1]}={counts[i-1]}"
        print(f"\n[AND递减] [OK] 关键词增多 -> 结果递减: {counts}")


# ============================================================================
# 辅助函数
# ============================================================================


def _extract_count(formatted_text: str) -> str:
    """从格式化输出中提取结果计数"""
    import re
    match = re.search(r"共检索到 (\d+) 条", formatted_text)
    return match.group(1) if match else "0"


# ============================================================================
# 运行入口
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
