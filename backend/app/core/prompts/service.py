"""提示词服务（单例）。

提供提示词加载、渲染、列表、详情、reload 等功能。
"""

from typing import Optional

from app.core.prompts.loader import PromptLoader
from app.core.prompts.renderer import PromptRenderer, build_context
from app.core.prompts.schemas import (
    PromptCategory,
    PromptConfigFile,
    PromptInfo,
    PromptTemplate,
)
from app.core.settings import get_settings
from app.observability.logging import get_logger

logger = get_logger(__name__)

# 模块级单例
_instance: Optional["PromptService"] = None


def get_prompt_service() -> "PromptService":
    """获取 PromptService 单例。"""
    global _instance
    if _instance is None:
        _instance = PromptService()
    return _instance


class PromptService:
    """提示词服务单例。"""

    def __init__(self) -> None:
        self._config: Optional[PromptConfigFile] = None

    # ─────────────────────────────────────────────────────────────
    # 生命周期
    # ─────────────────────────────────────────────────────────────

    async def init(self) -> None:
        """初始化：加载并校验提示词配置。

        启动失败时抛出，FastAPI lifespan 会拒绝启动。
        """
        settings = get_settings()
        config_path = settings.prompts.config_path

        logger.info("prompt_service_init_start", config_path=config_path)

        loader = PromptLoader(config_path)
        self._config = loader.load()

        logger.info(
            "prompt_service_init_ok",
            prompt_count=len(self._config.prompts),
            default_type=self._config.default_type,
        )

    # ─────────────────────────────────────────────────────────────
    # 读取
    # ─────────────────────────────────────────────────────────────

    def list_info(self) -> list[PromptInfo]:
        """返回所有提示词的公开信息（不含 content/variables）。"""
        if self._config is None:
            return []
        return [PromptInfo.from_template(p) for p in self._config.prompts]

    def get_prompt(self, type_id: str) -> Optional[PromptTemplate]:
        """根据 type_id 查找提示词模板。"""
        if self._config is None:
            return None
        for p in self._config.prompts:
            if p.id == type_id:
                return p
        return None

    def default_type(self) -> str:
        """返回默认提示词类型。"""
        if self._config is None:
            return "default"
        return self._config.default_type

    def categories(self) -> list[PromptCategory]:
        """返回所有不同的分类。"""
        if self._config is None:
            return []
        seen: set[str] = set()
        result: list[PromptCategory] = []
        for p in self._config.prompts:
            if p.category not in seen:
                seen.add(p.category)
                result.append(PromptCategory(p.category))
        return result

    # ─────────────────────────────────────────────────────────────
    # Reload
    # ─────────────────────────────────────────────────────────────

    async def reload(self) -> int:
        """重新加载提示词配置，返回提示词数量。"""
        settings = get_settings()
        loader = PromptLoader(settings.prompts.config_path)
        self._config = loader.load()
        logger.info("prompt_service_reload_ok", count=len(self._config.prompts))
        return len(self._config.prompts)

    # ─────────────────────────────────────────────────────────────
    # 解析 system prompt
    # ─────────────────────────────────────────────────────────────

    def resolve_system_prompt(
        self,
        override: Optional[str],
        prompt_id: Optional[str],
        session_id: str,
    ) -> tuple[str, str]:
        """解析 system prompt 内容。

        优先级：override > prompt_id > default_type

        Args:
            override: 手动传入的 system prompt（最高优先）
            prompt_id: 当前会话的提示词类型
            session_id: 会话 ID（用于日志）

        Returns:
            (rendered_system_text, used_prompt_id)
        """
        # 优先级 1: override
        if override is not None:
            logger.info(
                "chat_prompt_resolved",
                prompt_id="override",
                session_id=session_id,
            )
            return override, "override"

        # 优先级 2: prompt_id
        target_id = prompt_id

        if target_id:
            prompt = self.get_prompt(target_id)
            if prompt is not None:
                rendered = self._render_prompt(prompt)
                logger.info(
                    "chat_prompt_resolved",
                    prompt_id=target_id,
                    session_id=session_id,
                )
                return rendered, target_id
            else:
                # 静默回退到 default_type
                logger.warning(
                    "prompt_id_fallback",
                    requested=target_id,
                    used=self.default_type(),
                    session_id=session_id,
                )
        else:
            logger.info(
                "chat_prompt_resolved",
                prompt_id=self.default_type(),
                session_id=session_id,
            )

        # 优先级 3: default_type
        default_prompt = self.get_prompt(self.default_type())
        if default_prompt is not None:
            rendered = self._render_prompt(default_prompt)
            return rendered, self.default_type()

        # 兜底：硬编码
        logger.error("prompt_fallback_exhausted", session_id=session_id)
        return "你是一个友好的 AI 助手。", self.default_type()

    # ─────────────────────────────────────────────────────────────
    # 内部
    # ─────────────────────────────────────────────────────────────

    def _render_prompt(self, prompt: PromptTemplate) -> str:
        """渲染提示词模板。"""
        context = build_context()
        # 补充变量默认值
        for var in prompt.variables:
            if var.name not in context and var.default:
                context[var.name] = var.default
        return PromptRenderer.render_prompt(prompt.content, context)