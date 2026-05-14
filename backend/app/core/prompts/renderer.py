"""提示词模板渲染器。

使用 {variable} 语法。未声明的占位符保留原样。
"""

import re
from datetime import datetime, timedelta, timezone
from typing import Any


class PromptRenderer:
    """提示词模板渲染器。"""

    # 匹配 {variable_name} 形式的占位符
    _PLACEHOLDER_PATTERN = re.compile(r"\{([^}]+)\}")

    @classmethod
    def render_prompt(
        cls,
        content: str,
        context: dict[str, Any],
    ) -> str:
        """渲染提示词模板。

        Args:
            content: 提示词正文，支持 {variable} 占位符
            context: 变量上下文字典

        Returns:
            渲染后的提示词文本，未声明的占位符保持不变
        """

        def replacer(match: re.Match[str]) -> str:
            var_name = match.group(1)
            value = context.get(var_name)
            if value is None:
                # 未提供则保留原占位符
                return match.group(0)
            # datetime 等非字符串类型转为字符串
            if isinstance(value, datetime):
                return value.strftime("%Y-%m-%d %H:%M")
            return str(value)

        return cls._PLACEHOLDER_PATTERN.sub(replacer, content)


def build_context(
    user_name: str = "用户",
) -> dict[str, Any]:
    """构建渲染上下文。

    使用 UTC+8 时区。

    Args:
        user_name: 用户名，默认为"用户"

    Returns:
        包含 user_name 和 current_time（datetime） 的字典
    """
    utc8 = timezone(timedelta(hours=8))
    return {
        "user_name": user_name,
        "current_time": datetime.now(utc8),
    }