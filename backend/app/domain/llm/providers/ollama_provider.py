"""Domain LLM Providers 模块 - Ollama Provider 实现和模型发现。"""

import json
import time
from typing import AsyncGenerator, List, Optional

import httpx

from app.core.settings import get_settings
from app.domain.llm.providers.base import (
    LLMProviderProtocol,
    LLMResponse,
)


# ============================================================================
# Ollama 模型发现（保留原有功能）
# ============================================================================

# 缓存
_CACHE_TTL_MS = 30_000
_FETCH_TIMEOUT_MS = 2_000

_cache: dict = {"models": [], "expires_at": 0}


def _resolve_ollama_base() -> str:
    """从配置推导 Ollama 原生根地址。

    例：'http://localhost:11434/v1' → 'http://localhost:11434'
    """
    settings = get_settings()
    raw = settings.llm.ollama_base_url
    if not raw:
        return "http://localhost:11434"
    try:
        from urllib.parse import urlparse
        parsed = urlparse(raw)
        return f"{parsed.scheme}://{parsed.netloc}"
    except Exception:
        return "http://localhost:11434"


async def list_local_models() -> List[str]:
    """拉取本地 Ollama 已下载的模型 ID 列表。

    Returns:
        模型 ID 列表
    """
    global _cache

    # 缓存命中
    if _cache["models"] and _cache["expires_at"] > 0:
        if time.time() * 1000 < _cache["expires_at"]:
            return _cache["models"]

    base = _resolve_ollama_base()
    timeout = httpx.Timeout(_FETCH_TIMEOUT_MS / 1000, connect=1.0)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(f"{base}/api/tags")
            if response.status_code != 200:
                return _get_empty_cache()

            data = response.json()
            models_data = data.get("models", [])
            if not isinstance(models_data, list):
                return _get_empty_cache()

            ids = [
                m.get("name")
                for m in models_data
                if isinstance(m, dict)
                and isinstance(m.get("name"), str)
                and len(m["name"]) > 0
            ]

            # 更新缓存
            _cache = {
                "models": ids,
                "expires_at": time.time() * 1000 + _CACHE_TTL_MS,
            }
            return ids

    except (httpx.TimeoutException, httpx.ConnectError, Exception):
        return _get_empty_cache()


def _get_empty_cache() -> List[str]:
    """返回空缓存（不更新缓存）。"""
    global _cache
    if not _cache["models"]:
        _cache["expires_at"] = time.time() * 1000 + _CACHE_TTL_MS
    return []


def reset_cache_for_tests() -> None:
    """仅供测试使用：清空模块级缓存。"""
    global _cache
    _cache = {"models": [], "expires_at": 0}


# ============================================================================
# Ollama Provider
# ============================================================================


class OllamaProvider(LLMProviderProtocol):
    """Ollama 本地模型 Provider（使用 OpenAI 兼容端点）。"""

    def __init__(self) -> None:
        self._settings = get_settings()

    @property
    def name(self) -> str:
        return "ollama"

    def get_api_config(self) -> dict:
        base_url = self._settings.llm.ollama_base_url
        # 自动补全 /v1 后缀（OpenAI 兼容端点）
        if not base_url.rstrip("/").endswith("/v1"):
            base_url = f"{base_url.rstrip('/')}/v1"
        return {
            "api_base": base_url,
            "api_key": None,  # Ollama 本地部署不需要 Key
            "timeout": self._settings.llm.ollama_timeout,
            "default_model": self._settings.llm.ollama_model,
        }

    async def stream(
        self,
        messages: list,
        model: Optional[str] = None,
    ) -> AsyncGenerator[LLMResponse, None]:
        """调用 Ollama API（使用 OpenAI 兼容端点 /v1/chat/completions）。"""
        config = self.get_api_config()
        base_url = config["api_base"]
        model = model or config["default_model"]
        timeout = httpx.Timeout(config["timeout"], connect=5.0)

        # 过滤空消息
        ollama_messages = [
            {"role": m["role"], "content": m["content"]}
            for m in messages
            if m.get("content")
        ]

        payload = {
            "model": model,
            "messages": ollama_messages,
            "stream": True,
        }

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                async with client.stream(
                    "POST",
                    f"{base_url.rstrip('/')}/chat/completions",
                    json=payload,
                ) as response:
                    if response.status_code != 200:
                        error_body = await response.aread()
                        yield LLMResponse(
                            error=f"Ollama API error {response.status_code}: "
                            f"model={model}, response={error_body.decode('utf-8', errors='replace')[:200]}"
                        )
                        return

                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                yield LLMResponse(done=True)
                                break
                            try:
                                chunk = json.loads(data)
                                delta = chunk.get("choices", [{}])[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield LLMResponse(content=content)
                            except json.JSONDecodeError:
                                continue

        except httpx.TimeoutException:
            yield LLMResponse(error="Ollama request timeout")
        except httpx.ConnectError as e:
            yield LLMResponse(error=f"Ollama connection failed (is Ollama running?): {e}")


__all__ = [
    "OllamaProvider",
    "list_local_models",
    "reset_cache_for_tests",
]