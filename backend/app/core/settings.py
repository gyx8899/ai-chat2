"""Core 模块 - 应用配置。

重构自 app/config.py - 采用 DDD 分层架构。
使用 Pydantic Settings 集中管理所有配置。
"""

import os
from enum import Enum
from functools import lru_cache
from typing import Literal, Optional

from pydantic_settings import BaseSettings


class LLMProvider(str, Enum):
    """LLM Provider 枚举。"""

    MOCK = "mock"
    OPENAI = "openai"
    OLLAMA = "ollama"


class DatabaseSettings(BaseSettings):
    """数据库配置。"""

    url: str = "sqlite+aiosqlite:///./data/chat.db"
    echo: bool = False
    pool_size: int = 10
    max_overflow: int = 20
    pool_pre_ping: bool = True

    class Config:
        env_prefix = "DATABASE_"
        env_file = ".env"


class LLMSettings(BaseSettings):
    """LLM Provider 配置。"""

    provider: LLMProvider = LLMProvider.MOCK
    model: Optional[str] = "gpt-4o-mini"
    api_base: Optional[str] = "https://api.openai.com/v1"
    api_key: Optional[str] = ""
    timeout: float = 60.0
    stream_delay: float = 0.025  # 打字机延迟（秒）

    # OpenAI 特定配置
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = "https://api.openai.com/v1"
    openai_timeout: float = 60.0

    # Ollama 特定配置
    ollama_model: str = "llama3.2"
    ollama_base_url: str = "http://localhost:11434"
    ollama_timeout: float = 120.0

    class Config:
        env_prefix = "LLM_"
        env_file = ".env"


class ServerSettings(BaseSettings):
    """服务器配置。"""

    host: str = "0.0.0.0"
    port: int = 3001
    reload: bool = False

    class Config:
        env_prefix = "SERVER_"
        env_file = ".env"


class APISettings(BaseSettings):
    """API 配置。"""

    version: str = "v1"
    prefix: str = "/api/v1"
    title: str = "AI Chat API"
    description: str = "AI 对话应用后端 API - Next.js SSR + FastAPI + PostgreSQL"
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:3000"]

    class Config:
        env_prefix = "API_"
        env_file = ".env"


class PromptSettings(BaseSettings):
    """提示词配置。"""

    config_path: str = "config/prompts.json"
    frontend_url: str = "http://localhost:3000"
    revalidate_secret: str = "revalidate-secret-change-me"
    reload_secret: str = "reload-secret-change-me"

    class Config:
        env_prefix = "PROMPT_"
        env_file = ".env"


class Settings(BaseSettings):
    """应用全局配置。"""

    database: DatabaseSettings = DatabaseSettings()
    llm: LLMSettings = LLMSettings()
    server: ServerSettings = ServerSettings()
    api: APISettings = APISettings()
    prompts: PromptSettings = PromptSettings()

    # 应用元数据
    app_name: str = "ai-chat-next-python"
    title: str = "AI Chat API"
    version: str = "0.1.0"

    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"


@lru_cache()
def get_settings() -> Settings:
    """获取全局配置实例（单例）。"""
    return Settings()


# 快捷访问
settings = get_settings()


def get_current_config() -> dict:
    """获取当前 LLM 配置（供路由使用）。"""
    s = get_settings()
    return {
        "provider": s.llm.provider,
        "model": s.llm.model,
        "api_base": s.llm.api_base,
        "api_key": s.llm.api_key,
    }


# 向后兼容别名
__all__ = [
    "LLMProvider",
    "DatabaseSettings",
    "LLMSettings",
    "ServerSettings",
    "APISettings",
    "PromptSettings",
    "Settings",
    "get_settings",
    "settings",
    "get_current_config",
]