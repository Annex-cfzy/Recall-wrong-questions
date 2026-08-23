"""Error (错题) model with SM-2 spaced-repetition fields."""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Float,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class Error(Base):
    __tablename__ = "errors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    notebook_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("notebooks.id", ondelete="CASCADE"), nullable=False
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    analysis: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    knowledge_points: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # JSON array string
    subject: Mapped[str] = mapped_column(String(60), nullable=False, default="通用")
    source: Mapped[str] = mapped_column(String(16), nullable=False, default="manual")
    image_path: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # SM-2 parameters
    mastery: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    repetition: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    interval_days: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    ease_factor: Mapped[float] = mapped_column(Float, nullable=False, default=2.5)
    next_review: Mapped[date] = mapped_column(Date, nullable=False)
    last_review: Mapped[date | None] = mapped_column(Date, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    notebook: Mapped["Notebook"] = relationship(  # noqa: F821
        "Notebook", back_populates="errors"
    )
    review_records: Mapped[list["ReviewRecord"]] = relationship(  # noqa: F821
        "ReviewRecord", back_populates="error", cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "notebook_id": self.notebook_id,
            "question": self.question,
            "answer": self.answer,
            "analysis": self.analysis,
            "error_cause": self.error_cause,
            "knowledge_points": _parse_json(self.knowledge_points),
            "subject": self.subject,
            "source": self.source,
            "image_path": self.image_path,
            "mastery": self.mastery,
            "repetition": self.repetition,
            "interval_days": self.interval_days,
            "ease_factor": self.ease_factor,
            "next_review": self.next_review.isoformat() if self.next_review else None,
            "last_review": self.last_review.isoformat() if self.last_review else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


def _parse_json(value: str | None):
    if not value:
        return []
    import json

    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return []
