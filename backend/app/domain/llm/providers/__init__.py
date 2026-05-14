"""Domain LLM Providers 模块 - 初始化。

导出所有 Provider 并注册到全局注册表。
"""

from app.domain.llm.providers.base import (
    get_provider_registry,
    provider_registry,
)
from app.domain.llm.providers.mock import MockProvider
from app.domain.llm.providers.openai import OpenAIProvider
from app.domain.llm.providers.ollama_provider import OllamaProvider


def _register_providers() -> None:
    """注册所有 Provider 到全局注册表。"""
    registry = get_provider_registry()

    # 注册 Provider 实例
    registry.register(MockProvider())
    registry.register(OpenAIProvider())
    registry.register(OllamaProvider())

    # 注册模型前缀 -> Provider 映射
    # OpenAI 风格模型
    registry.register_model_prefix("gpt-", "openai")
    registry.register_model_prefix("text-", "openai")
    registry.register_model_prefix("embedding-", "openai")
    registry.register_model_prefix("o1-", "openai")
    registry.register_model_prefix("chatgpt-", "openai")

    # Ollama 本地模型（默认）
    registry.register_model_prefix("llama", "ollama")
    registry.register_model_prefix("qwen", "ollama")
    registry.register_model_prefix("deepseek", "ollama")
    registry.register_model_prefix("gemma", "ollama")
    registry.register_model_prefix("mistral", "ollama")
    registry.register_model_prefix("phi", "ollama")


# 启动时自动注册
_register_providers()


__all__ = [
    "get_provider_registry",
    "provider_registry",
    "MockProvider",
    "OpenAIProvider",
    "OllamaProvider",
]