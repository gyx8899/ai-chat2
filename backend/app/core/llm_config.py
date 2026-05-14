"""Core 模块 - LLM 配置管理。

支持多 API Key 映射和模型默认配置。
"""

from typing import Optional

from app.core.settings import get_settings


class LLMConfigManager:
    """LLM 配置管理器。

    支持：
    - 多 API Key 映射（不同模型使用不同的 Key）
    - 模型默认 Base URL 配置
    - Provider 自动推断
    """

    # 模型 -> API Key 环境变量名映射
    MODEL_API_KEY_MAPPING: dict[str, str] = {
        "gpt-4o": "OPENAI_API_KEY",
        "gpt-4o-mini": "OPENAI_API_KEY",
        "deepseek-v3": "DEEPSEEK_API_KEY",
        "qwen-max": "QWEN_API_KEY",
    }

    # 模型 -> Base URL 映射（优先级：用户配置 > 模型默认 > 全局默认）
    MODEL_BASE_URLS: dict[str, str] = {
        "gpt-4o": "https://api.openai.com/v1",
        "gpt-4o-mini": "https://api.openai.com/v1",
        "deepseek-v3": "https://api.deepseek.com/v1",
        "qwen-max": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    }

    def __init__(self) -> None:
        import os
        self._os = os

    def get_api_key(self, model: Optional[str] = None) -> Optional[str]:
        """获取 API Key。

        Args:
            model: 模型名称（可选）

        Returns:
            API Key 字符串
        """
        settings = get_settings()

        # 如果指定了模型，优先使用模型专属配置
        if model:
            env_key_name = self.MODEL_API_KEY_MAPPING.get(model)
            if env_key_name:
                key = self._os.environ.get(env_key_name)
                if key:
                    return key

        # Fallback 到全局 API Key
        return settings.llm.api_key or self._os.environ.get("OPENAI_API_KEY")

    def get_base_url(self, model: Optional[str] = None) -> str:
        """获取 Base URL。

        Args:
            model: 模型名称（可选）

        Returns:
            Base URL 字符串
        """
        settings = get_settings()

        # 如果指定了模型，优先使用模型默认配置
        if model and model in self.MODEL_BASE_URLS:
            return self.MODEL_BASE_URLS[model]

        # Fallback 到用户配置的 Base URL
        user_base = settings.llm.api_base
        if user_base:
            return user_base

        # 默认 OpenAI URL
        return "https://api.openai.com/v1"

    def get_model_for_provider(self, provider: str, preferred_model: Optional[str] = None) -> str:
        """获取 Provider 对应的模型名称。

        Args:
            provider: Provider 名称
            preferred_model: 首选模型（可选）

        Returns:
            模型名称
        """
        settings = get_settings()

        if preferred_model:
            return preferred_model

        if provider == "openai":
            return settings.llm.openai_model or "gpt-4o-mini"
        elif provider == "ollama":
            return settings.llm.ollama_model or "llama3.2"

        return settings.llm.model or "gpt-4o-mini"


# 全局实例
_llm_config_manager: Optional[LLMConfigManager] = None


def get_llm_config_manager() -> LLMConfigManager:
    """获取 LLM 配置管理器实例。"""
    global _llm_config_manager
    if _llm_config_manager is None:
        _llm_config_manager = LLMConfigManager()
    return _llm_config_manager


__all__ = [
    "LLMConfigManager",
    "get_llm_config_manager",
]