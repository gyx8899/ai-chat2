"""提示词配置的 Pydantic 模型定义"""

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class PromptVariable(BaseModel):
    """模板变量定义"""

    name: str = Field(..., description="变量名称，如 user_name")
    description: str = Field(..., description="变量用途描述")
    default: Optional[str] = Field(default="", description="变量默认值")


class PromptTemplate(BaseModel):
    """完整的提示词模板（内部使用）"""

    id: str = Field(..., description="唯一标识符，URL type 参数值")
    type: str = Field(..., description="类型标识，同 id")
    name: str = Field(..., description="显示名称")
    description: str = Field(..., description="简短描述")
    category: str = Field(..., description="分类")
    content: str = Field(..., description="提示词正文内容（支持 {variable} 模板语法）")
    variables: list[PromptVariable] = Field(default_factory=list, description="变量列表")
    welcome: str = Field(default="", description="欢迎语")
    examples: list[str] = Field(default_factory=list, description="示例问题列表")
    preferred_model: Optional[str] = Field(default=None, description="偏好模型")
    is_enabled: bool = Field(default=True, description="是否启用")

    model_config = {"extra": "forbid"}


class PromptInfo(BaseModel):
    """提示词公开信息（对外 API 下发，不含 content/variables）"""

    id: str = Field(..., description="唯一标识符")
    type: str = Field(..., description="类型标识")
    name: str = Field(..., description="显示名称")
    description: str = Field(..., description="简短描述")
    category: str = Field(..., description="分类")
    welcome: str = Field(default="", description="欢迎语")
    examples: list[str] = Field(default_factory=list, description="示例问题列表")
    preferred_model: Optional[str] = Field(default=None, description="偏好模型")
    is_enabled: bool = Field(default=True, description="是否启用")

    model_config = {"extra": "forbid"}

    @classmethod
    def from_template(cls, template: PromptTemplate) -> "PromptInfo":
        """从 PromptTemplate 转换而来，过滤掉敏感/内部字段"""
        return cls(
            id=template.id,
            type=template.type,
            name=template.name,
            description=template.description,
            category=template.category,
            welcome=template.welcome,
            examples=template.examples,
            preferred_model=template.preferred_model,
            is_enabled=template.is_enabled,
        )


class PromptCategory(str, Enum):
    """提示词分类枚举"""

    GENERAL = "general"
    DEVELOPMENT = "development"
    WRITING = "writing"


class PromptGlobalSettings(BaseModel):
    """提示词全局设置"""

    default_type: str = Field(..., description="默认提示词类型，值为 prompts[].type")


class PromptConfigFile(BaseModel):
    """完整的 prompts.json 文件结构"""

    prompts: list[PromptTemplate] = Field(..., description="提示词列表")
    default_type: str = Field(..., description="默认提示词类型")
    metadata: Optional[dict[str, Any]] = Field(default=None, description="元数据")

    model_config = {"extra": "allow"}