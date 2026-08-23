"""ReviewRecord (复习记录) model."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class ReviewRecord(Base):
    __tablename__ = "review_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    error_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("errors.id", ondelete="CASCADE"), nullable=False
    )
    variant_question: Mapped[str] = mapped_column(Text, nullable=False)
    user_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quality: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ai_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    error: Mapped["Error"] = relationship("Error", back_populates="review_records")  # noqa: F821

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "error_id": self.error_id,
            "variant_question": self.variant_question,
            "user_answer": self.user_answer,
            "is_correct": self.is_correct,
            "score": self.score,
            "quality": self.quality,
            "ai_feedback": self.ai_feedback,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
        }
