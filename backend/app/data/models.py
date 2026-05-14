"""Data 模块 - 可用模型配置。

重构自 app/data/models.py - 仅云端模型与 mock。
本地 Ollama 模型由 integrations/model_registry.py 动态发现。
"""

from dataclasses import dataclass
from typing import Literal


@dataclass
class Model:
    """模型配置。"""

    id: str
    name: str
    provider: Literal["mock", "openai", "ollama"]
    description: str
    icon: str


# 可用模型列表（云端 + mock）
AVAILABLE_MODELS: list[Model] = [
    Model(
        id="mock",
        name="Mock 模型",
        provider="mock",
        description="本地预设规则，无需 API Key，适合开发调试",
        icon="🤖",
    ),
    # Model(
    #     id="qwen-max",
    #     name="Qwen Max",
    #     provider="openai",
    #     description="阿里通义千问旗舰版，中文理解强",
    #     icon="🌟",
    # ),
]


__all__ = ["Model", "AVAILABLE_MODELS"]