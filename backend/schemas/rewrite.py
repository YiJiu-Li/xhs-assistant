"""改写接口 Pydantic 模型"""

from pydantic import BaseModel, Field
from config import DEFAULT_MODEL, DEFAULT_TEMPERATURE


class RewriteRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000, description="原始文案")
    style: str = Field(default="种草推荐", description="改写风格")
    model: str = Field(default=DEFAULT_MODEL)
    temperature: float = Field(default=DEFAULT_TEMPERATURE, ge=0.0, le=2.0)
    use_rag: bool = Field(default=False, description="是否使用知识库增强")


class HashtagRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000, description="文案内容")
    model: str = Field(default=DEFAULT_MODEL)
