"""Error schemas."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ErrorImportItem(BaseModel):
    question: str = Field(..., min_length=1)
    answer: str = ""
    notebook_id: int
    subject: str = "通用"
    source: str = "photo"
    image_path: str | None = None


class ErrorImportRequest(BaseModel):
    questions: list[ErrorImportItem]


class ErrorTextRequest(BaseModel):
    question: str = Field(..., min_length=1)
    answer: str = ""
    notebook_id: int
    subject: str = "通用"


class ErrorUpdate(BaseModel):
    question: str | None = None
    answer: str | None = None
    analysis: str | None = None
    error_cause: str | None = None
    knowledge_points: list[str] | None = None
    notebook_id: int | None = None
    subject: str | None = None


class ErrorListParams(BaseModel):
    """Query parameters for the error list endpoint."""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    notebook_id: int | None = None
    subject: str | None = None
    knowledge_points: str | None = None
    mastery_min: int | None = Field(default=None, ge=0, le=100)
    mastery_max: int | None = Field(default=None, ge=0, le=100)
    date_from: str | None = None
    date_to: str | None = None
    is_due: bool | None = None
    search: str | None = None
    sort: str = Field(default="created_at", pattern=r"^(created_at|mastery|next_review)$")
    order: str = Field(default="desc", pattern=r"^(asc|desc)$")
