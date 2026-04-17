"""对话接口 Pydantic 模型"""

from typing import List
from pydantic import BaseModel, Field
from config import DEFAULT_MODEL, DEFAULT_TEMPERATURE


class SessionInfo(BaseModel):
    session_id: str
    created_at: str
    message_count: int


class SessionListResponse(BaseModel):
    sessions: List[SessionInfo]


class CreateSessionResponse(BaseModel):
    session_id: str


class MessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    model: str = Field(default=DEFAULT_MODEL)
    temperature: float = Field(default=DEFAULT_TEMPERATURE)


class MessageRecord(BaseModel):
    role: str  # 'human' | 'ai'
    content: str


class HistoryResponse(BaseModel):
    session_id: str
    messages: List[MessageRecord]
