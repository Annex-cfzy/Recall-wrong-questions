"""Chat schemas."""
from __future__ import annotations

from pydantic import BaseModel, Field


class ChatSessionCreate(BaseModel):
    title: str = "新对话"


class ChatStreamRequest(BaseModel):
    session_id: int
    message: str = Field(..., min_length=1)


class ChatSaveRequest(BaseModel):
    message_id: int
    notebook_id: int
    subject: str = "通用"
