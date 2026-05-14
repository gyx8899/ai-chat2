"""提示词配置文件加载器。

两阶段校验：
1. 结构校验：Pydantic model_validate（schema/类型）
2. 业务校验：default_type 必须存在、id 唯一非空

仅"文件缺失"才降级到内置默认；结构/业务错误直接抛出 RuntimeError。
"""

import json
import os
import re

from app.core.prompts.schemas import (
    PromptConfigFile,
    PromptTemplate,
)
from app.observability.logging import get_logger

logger = get_logger(__name__)

# 内置降级提示词（文件缺失时使用）
_BUILTIN_FALLBACK = PromptConfigFile(
    prompts=[
        PromptTemplate(
            id="default",
            type="default",
            name="默认助手",
            description="通用 AI 助手",
            category="general",
            content="你是一个友好的 AI 助手。",
            variables=[],
            welcome="你好！有什么我可以帮助你的吗？",
            examples=[],
            preferred_model=None,
        )
    ],
    default_type="default",
    metadata={"source": "builtin_fallback"},
)


class PromptLoadError(RuntimeError):
    """提示词加载错误基类。"""

    pass


def _scan_undeclared_vars(content: str) -> list[str]:
    """扫描 content 中所有 {var} 占位符（排除空占位符 {}）。"""
    return re.findall(r"\{([^}]+)\}", content)


def warn_undeclared_variables(config: PromptConfigFile) -> None:
    """扫描所有 prompt 的 content，输出未声明变量的 WARN 日志。

    仅告警，不抛异常，不影响运行。
    """
    for prompt in config.prompts:
        declared = {v.name for v in prompt.variables}
        found = set(_scan_undeclared_vars(prompt.content))
        undeclared = found - declared
        if undeclared:
            logger.warning(
                "warn_undeclared_variables",
                prompt_id=prompt.id,
                undeclared_variables=sorted(undeclared),
            )


class PromptLoader:
    """提示词配置文件加载器。"""

    def __init__(self, config_path: str) -> None:
        self.config_path = config_path

    def load(self) -> PromptConfigFile:
        """加载并校验 prompts.json。

        Returns:
            PromptConfigFile: 已校验的配置对象

        Raises:
            RuntimeError: 结构校验或业务校验失败时抛出
        """
        # 阶段 1：文件存在性检查（仅此场景降级）
        if not os.path.exists(self.config_path):
            logger.error(
                "prompt_config_file_not_found",
                path=self.config_path,
                fallback="builtin_default",
            )
            return _BUILTIN_FALLBACK

        # 读取文件内容
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
        except json.JSONDecodeError as e:
            raise RuntimeError(
                f"prompt_config_parse_error: {e}"
            ) from e

        # 阶段 1：结构校验（Pydantic）
        try:
            config = PromptConfigFile.model_validate(raw)
        except Exception as e:
            raise RuntimeError(
                f"prompt_config_validation_error: {e}"
            ) from e

        # 阶段 2：业务校验
        self._validate_business(config)

        # 未声明变量警告（不抛错）
        warn_undeclared_variables(config)

        return config

    def _validate_business(self, config: PromptConfigFile) -> None:
        """业务校验：default_type 存在、id 唯一非空。"""
        # id 唯一性
        ids = [p.id for p in config.prompts]
        if len(ids) != len(set(ids)):
            seen: dict[str, int] = {}
            for i, pid in enumerate(ids):
                seen.setdefault(pid, i)
            duplicates = [k for k, v in {pid: ids.count(pid) for pid in set(ids)}.items() if v > 1]
            raise RuntimeError(
                f"prompt_config_business_error: duplicate prompt ids: {duplicates}"
            )

        # id 非空
        for p in config.prompts:
            if not p.id or not p.id.strip():
                raise RuntimeError(
                    "prompt_config_business_error: prompt id cannot be empty"
                )

        # default_type 必须存在于 prompts
        if config.default_type not in ids:
            raise RuntimeError(
                f"prompt_config_business_error: default_type '{config.default_type}' "
                f"not found in prompts. Available: {ids}"
            )