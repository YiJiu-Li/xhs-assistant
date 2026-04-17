"""批量处理接口 Pydantic 模型"""

from typing import List
from pydantic import BaseModel, Field
from config import FAST_MODEL, DEFAULT_TEMPERATURE, BATCH_MAX_SIZE


class BatchRequest(BaseModel):
    texts: List[str] = Field(..., min_length=1)
    style: str = Field(default="种草推荐")
    model: str = Field(default=FAST_MODEL)
    generate_tags: bool = Field(default=True)
