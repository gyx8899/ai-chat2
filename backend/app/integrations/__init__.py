"""Integrations 模块 - 外部集成层。

提供模型注册表和 RAG 服务。
采用 DDD 分层架构。
"""

import re
from dataclasses import dataclass
from typing import Optional

from app.data.models import AVAILABLE_MODELS, Model as BaseModel
from app.domain.llm.providers.ollama_provider import list_local_models

# 模型 family → icon 映射规则（按顺序优先匹配）
ICON_RULES: list[tuple[str, str]] = [
    (r"^qwen", "🌟"),
    (r"^deepseek", "🧠"),
    (r"^llama", "🦙"),
    (r"^gemma", "💎"),
    (r"^mistral", "🌬️"),
    (r"^phi", "🔹"),
    (r"^codellama", "🦙"),
]

DEFAULT_ICON = "🤖"


def infer_icon(model_id: str) -> str:
    """根据模型 ID 推断 icon（按 family 匹配）。"""
    if not isinstance(model_id, str):
        return DEFAULT_ICON
    for pattern, icon in ICON_RULES:
        if re.match(pattern, model_id, re.IGNORECASE):
            return icon
    return DEFAULT_ICON


def prettify_name(model_id: str) -> str:
    """美化模型名：`qwen3.5:0.8b` → `Qwen 3.5 (0.8B)`。

    - 无 `:tag` 时仅做分词与首字母大写
    - 参数规模 tag（如 `0.8b` / `8b`）统一转大写
    - 非规模 tag（如 `instruct` / `latest`）保留原样
    - 处理常见 brand 大小写（DeepSeek / GPT 等）
    """
    if not isinstance(model_id, str) or len(model_id) == 0:
        return ""

    base, _, tag = model_id.partition(":")

    # 分词规则：
    # 1. `-` / `_` 拆成独立单词
    # 2. 仅当 ≥2 个字母紧跟数字时插入空格（避免 'r1'/'v2' 等短版本号被拆散）
    # 3. 数字后紧跟字母不拆（保留 '7b' / '0.8b' 等规模后缀完整性，由 tag 处理）
    with_spaces = re.sub(r"[-_]", " ", base)
    with_spaces = re.sub(r"([a-zA-Z]{2,})(\d)", r"\1 \2", with_spaces)

    # 每个单词首字母大写 + 已知 brand 修正
    BRAND_CASE = {
        "Deepseek": "DeepSeek",
        "Gpt": "GPT",
        "Openai": "OpenAI",
        "Codellama": "CodeLlama",
    }
    upper_base = " ".join(
        BRAND_CASE.get(capitalized, capitalized)
        for word in with_spaces.split()
        if word
        for capitalized in [word[0].upper() + word[1:].lower()]
    )

    if not tag:
        return upper_base

    # 规模 tag 转为大写，非规模 tag 保留原样
    tag_fmt = tag.upper() if re.match(r"^[\d.]+b$", tag, re.IGNORECASE) else tag
    return f"{upper_base} ({tag_fmt})"


def build_ollama_model_entry(model_id: str) -> dict:
    """构造 Ollama 模型条目（符合前端 Model 类型契约）。"""
    return {
        "id": model_id,
        "name": prettify_name(model_id),
        "provider": "ollama",
        "description": f"本地 Ollama 部署：{model_id}",
        "icon": infer_icon(model_id),
    }


async def build_model_list() -> list[dict]:
    """构造最终模型列表：硬编码云端模型 + 动态发现的 Ollama 模型。

    降级契约：当 list_local_models() 返回 [] 时（Ollama 不可达），
    仅返回 AVAILABLE_MODELS（云端 + mock），不抛错。

    Returns:
        模型列表（每个元素包含 id, name, provider, description, icon）
    """
    # 获取 Ollama 模型
    ollama_ids = await list_local_models()
    ollama_models = [build_ollama_model_entry(mid) for mid in ollama_ids]

    # 合并云端模型
    from dataclasses import asdict

    cloud_models = [asdict(m) for m in AVAILABLE_MODELS]

    return ollama_models + cloud_models


def get_model_by_id(model_id: str, models: list[dict]) -> Optional[dict]:
    """根据 ID 查找模型。"""
    return next((m for m in models if m["id"] == model_id), None)


__all__ = [
    "build_model_list",
    "get_model_by_id",
    "infer_icon",
    "prettify_name",
]