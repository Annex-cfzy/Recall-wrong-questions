"""Notebook schemas."""
from __future__ import annotations

from pydantic import BaseModel, Field


class NotebookCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    subject: str = Field(default="通用", max_length=60)
    color: str = Field(default="#007AFF", pattern=r"^#[0-9A-Fa-f]{6}$")


class NotebookUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    subject: str | None = Field(default=None, max_length=60)
    color: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")


class NotebookResponse(BaseModel):
    id: int
    name: str
    subject: str
    color: str
    error_count: int = 0
    created_at: str | None = None
    updated_at: str | None = None
