"""Review schemas."""
from __future__ import annotations

from pydantic import BaseModel, Field


class ReviewStartRequest(BaseModel):
    subject: str | None = None
    notebook_id: int | None = None
    count: int = Field(default=10, ge=1, le=50)


class ReviewAnswerItem(BaseModel):
    error_id: int
    index: int
    user_answer: str = ""


class ReviewSubmitRequest(BaseModel):
    review_id: str
    answers: list[ReviewAnswerItem]
