"""知识库接口 Pydantic 模型"""

from typing import Optional
from pydantic import BaseModel, Field


class AddDocRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1, max_length=5000)
    style: str = Field(default="种草推荐")
    hashtags: str = Field(default="")


class UpdateDocRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1, max_length=5000)
    style: str = Field(default="种草推荐")
    hashtags: str = Field(default="")


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    style: Optional[str] = Field(default=None)
    top_k: int = Field(default=3, ge=1, le=10)


class DocItem(BaseModel):
    id: str
    title: str
    style: str
    source: str
    hashtags: str
    content: str
    content_preview: str
