"""SQLAlchemy declarative models.

`Base` is defined here and all model modules import it; importing this
package registers every model with the metadata (used by `init_db`).
"""
from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from app.models.notebook import Notebook  # noqa: E402,F401
from app.models.error import Error  # noqa: E402,F401
from app.models.review import ReviewRecord  # noqa: E402,F401
from app.models.chat import ChatSession, ChatMessage  # noqa: E402,F401
