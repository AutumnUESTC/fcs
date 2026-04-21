"""公共 LLM 工厂 - 统一管理 LLM 实例的创建

支持两种模式：
  - Mock 模式：不依赖真实 LLM，Planner 内部用预设策略模拟 ReAct 行为
  - LLM 模式：通过环境变量或硬编码配置接入混元大模型

接入混元（OpenAI 兼容模式）：
  1. pip install langchain-openai
  2. 在下方 _HUNYUAN_API_KEY 填入你的 API Key，或设置环境变量 HUNYUAN_API_KEY
  3. get_llm() 自动返回 ChatOpenAI 实例，base_url 指向混元

配置优先级：环境变量 > 代码中的默认值
"""

from __future__ import annotations

import os
from typing import Any

# ===========================================================================
# 混元 API 配置（直接修改这里的值即可，无需设置环境变量）
# ===========================================================================

# 混元 API Key — 在 https://console.cloud.tencent.com/hunyuan 的 API Key 管理页获取
_HUNYUAN_API_KEY: str = os.getenv("HUNYUAN_API_KEY", "sk-EbZZmpd8fS42zjgi6T9wl2xPjmgYcN98IIV3nD7r3GJAYdIb")

# 混元 API 地址（OpenAI 兼容接口）
_HUNYUAN_BASE_URL: str = os.getenv(
    "HUNYUAN_BASE_URL",
    "https://api.hunyuan.cloud.tencent.com/v1",
)

# 默认模型名称
# 可选值：hunyuan-turbos-latest / hunyuan-lite / hunyuan-turbos / hunyuan-functioncall
_HUNYUAN_DEFAULT_MODEL: str = os.getenv("LLM_MODEL", "hunyuan-lite")

# 温度参数（0 = 确定性输出，越高越随机）
_HUNYUAN_DEFAULT_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0"))

# 最大并发数（混元默认限制 5 并发）
_HUNYUAN_MAX_CONCURRENCY: int = int(os.getenv("LLM_MAX_CONCURRENCY", "5"))

# ===========================================================================
# LLM 实例管理
# ===========================================================================

# 缓存 LLM 实例（避免重复创建）
_llm_instance: Any = None


def get_llm(**kwargs: Any) -> Any:
    """获取 LLM 实例

    如果 _HUNYUAN_API_KEY 不为空，返回 ChatOpenAI 实例
    （通过 OpenAI 兼容接口接入混元）。
    否则返回 None，Planner 内部走 Mock 模式。

    Args:
        **kwargs: 可选的覆盖参数，如 model, temperature, base_url 等

    Returns:
        ChatOpenAI 实例 或 None
    """
    global _llm_instance

    api_key = _HUNYUAN_API_KEY

    # 没有 API Key → Mock 模式
    if not api_key:
        return None

    # 有 API Key → 创建或复用 LLM 实例
    if _llm_instance is not None and not kwargs:
        return _llm_instance

    try:
        from langchain_openai import ChatOpenAI
    except ImportError:
        raise ImportError(
            "使用混元 LLM 需要 langchain-openai，请运行：\n"
            "  pip install langchain-openai"
        )

    model = kwargs.get("model", _HUNYUAN_DEFAULT_MODEL)
    temperature = kwargs.get("temperature", _HUNYUAN_DEFAULT_TEMPERATURE)
    base_url = kwargs.get("base_url", _HUNYUAN_BASE_URL)

    llm = ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=api_key,
        base_url=base_url,
    )

    # 缓存无自定义参数的实例
    if not kwargs:
        _llm_instance = llm

    return llm


def is_mock_mode() -> bool:
    """判断当前是否为 mock 模式

    _HUNYUAN_API_KEY 为空时返回 True（Mock 模式）
    """
    return _HUNYUAN_API_KEY == ""


def reset_llm() -> None:
    """重置缓存的 LLM 实例（用于切换配置后重新创建）"""
    global _llm_instance
    _llm_instance = None


def configure(
    api_key: str = "",
    base_url: str = "",
    model: str = "",
    temperature: float | None = None,
) -> None:
    """运行时动态修改混元配置

    Args:
        api_key: 混元 API Key
        base_url: 混元 API 地址
        model: 模型名称
        temperature: 温度参数
    """
    global _HUNYUAN_API_KEY, _HUNYUAN_BASE_URL, _HUNYUAN_DEFAULT_MODEL, _HUNYUAN_DEFAULT_TEMPERATURE

    if api_key:
        _HUNYUAN_API_KEY = api_key
    if base_url:
        _HUNYUAN_BASE_URL = base_url
    if model:
        _HUNYUAN_DEFAULT_MODEL = model
    if temperature is not None:
        _HUNYUAN_DEFAULT_TEMPERATURE = temperature

    # 配置变更后重置缓存实例
    reset_llm()
