"""Notebook (错题本) model."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class Notebook(Base):
    __tablename__ = "notebooks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    subject: Mapped[str] = mapped_column(String(60), nullable=False, default="通用")
    color: Mapped[str] = mapped_column(String(16), nullable=False, default="#007AFF")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    errors: Mapped[list["Error"]] = relationship(  # noqa: F821
        "Error", back_populates="notebook", cascade="all, delete-orphan"
    )

    def to_dict(self, error_count: int = 0) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "subject": self.subject,
            "color": self.color,
            "error_count": error_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
