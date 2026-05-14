"""Domain LLM Providers 模块 - Provider 抽象基类。

采用策略模式，支持运行时注册新的 LLM Provider。
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncGenerator, Optional, Union

import httpx

from app.core.settings import get_settings


@dataclass
class LLMResponse:
    """LLM 流式响应帧。"""
    content: str = ""  # 内容帧
    error: Optional[str] = None  # 错误帧
    done: bool = False  # 是否结束
    meta: Optional[dict] = None  # 元数据帧


class LLMProviderProtocol(ABC):
    """LLM Provider 抽象接口。

    所有 LLM Provider 必须实现此接口。
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider 名称（唯一标识）。"""
        ...

    @abstractmethod
    async def stream(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
    ) -> AsyncGenerator[LLMResponse, None]:
        """流式生成响应。

        Args:
            messages: 消息列表
            model: 模型名称（可选，Provider 可使用自己的默认模型）

        Yields:
            LLMResponse 流式响应帧
        """
        ...

    @abstractmethod
    def get_api_config(self) -> dict:
        """获取 Provider 的 API 配置。

        Returns:
            包含 api_base, api_key, timeout 等配置
        """
        ...


@dataclass
class ProviderRegistry:
    """Provider 注册表（策略模式核心）。"""
    _providers: dict[str, LLMProviderProtocol] = field(default_factory=dict)
    _model_prefixes: dict[str, str] = field(default_factory=dict)  # 模型前缀 -> provider 名称
    _default_provider: str = "mock"

    def register(self, provider: LLMProviderProtocol) -> None:
        """注册 Provider。

        Args:
            provider: Provider 实例
        """
        self._providers[provider.name] = provider

    def register_model_prefix(self, prefix: str, provider_name: str) -> None:
        """注册模型前缀到 Provider 的映射。

        Args:
            prefix: 模型前缀（如 "gpt-"、"llama"）
            provider_name: Provider 名称
        """
        self._model_prefixes[prefix] = provider_name

    def get(self, name: str) -> LLMProviderProtocol | None:
        """根据名称获取 Provider。"""
        return self._providers.get(name)

    def resolve_provider(self, model: Optional[str]) -> str:
        """根据模型名称推断 Provider。

        Args:
            model: 模型名称

        Returns:
            Provider 名称
        """
        if not model:
            return self._default_provider

        # 前缀匹配
        for prefix, provider_name in self._model_prefixes.items():
            if model.startswith(prefix):
                return provider_name

        return self._default_provider

    def list_providers(self) -> list[str]:
        """列出所有已注册的 Provider。"""
        return list(self._providers.keys())


# 全局注册表实例
provider_registry = ProviderRegistry()


def get_provider_registry() -> ProviderRegistry:
    """获取 Provider 注册表。"""
    return provider_registry


__all__ = [
    "LLMProviderProtocol",
    "LLMResponse",
    "ProviderRegistry",
    "provider_registry",
    "get_provider_registry",
]