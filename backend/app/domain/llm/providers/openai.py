"""Domain LLM Providers 模块 - OpenAI Provider 实现。"""

import json
from typing import AsyncGenerator, Optional

import httpx

from app.core.settings import get_settings
from app.core.exceptions import AppException, ErrorCode
from app.domain.llm.providers.base import (
    LLMProviderProtocol,
    LLMResponse,
)


class OpenAIProvider(LLMProviderProtocol):
    """OpenAI API Provider。"""

    def __init__(self) -> None:
        self._settings = get_settings()
        from app.core.llm_config import get_llm_config_manager
        self._config_manager = get_llm_config_manager()

    @property
    def name(self) -> str:
        return "openai"

    def get_api_config(self) -> dict:
        default_model = self._settings.llm.openai_model
        return {
            "api_base": self._config_manager.get_base_url(default_model),
            "api_key": self._config_manager.get_api_key(default_model),
            "timeout": self._settings.llm.openai_timeout,
            "default_model": default_model,
        }

    async def stream(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
    ) -> AsyncGenerator[LLMResponse, None]:
        """调用 OpenAI Chat Completions API（流式）。"""
        config = self.get_api_config()
        api_key = config["api_key"]
        base_url = config["api_base"]
        model = model or config["default_model"]
        timeout = httpx.Timeout(config["timeout"], connect=10.0)

        if not api_key:
            yield LLMResponse(error="OpenAI API key not configured")
            return

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
        }

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                async with client.stream(
                    "POST",
                    f"{base_url.rstrip('/')}/chat/completions",
                    headers=headers,
                    json=payload,
                ) as response:
                    if response.status_code == 429:
                        yield LLMResponse(error="OpenAI rate limit exceeded")
                        return
                    if response.status_code != 200:
                        error_body = await response.aread()
                        yield LLMResponse(
                            error=f"OpenAI API error {response.status_code}: "
                            f"{error_body.decode('utf-8', errors='replace')[:200]}"
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
            yield LLMResponse(error="OpenAI request timeout")
        except httpx.ConnectError as e:
            yield LLMResponse(error=f"OpenAI connection failed: {e}")


__all__ = ["OpenAIProvider"]