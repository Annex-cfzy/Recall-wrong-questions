"""SQLite connection + SQLAlchemy session management.

SQLite runs in WAL mode (see PRD risk R6) for better concurrent reads.
"""
from __future__ import annotations

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

connect_args = {"check_same_thread": False}
engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    pool_pre_ping=True,
    future=True,
)


@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):  # pragma: no cover
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Session:
    """FastAPI dependency that yields a session and closes it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables (and FTS5 virtual table) on first run."""
    import app.models  # noqa: F401  ensure models are registered
    from app.core.database import engine
    from sqlalchemy import text

    # Import Base via models package
    from app.models import Base

    Base.metadata.create_all(bind=engine)

    # FTS5 virtual table for full-text search over errors.
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS errors_fts USING fts5(
                    question, answer, analysis, knowledge_points,
                    content='errors', content_rowid='id'
                );
                """
            )
        )
        # Keep the FTS table in sync via triggers.
        conn.execute(
            text(
                """
                CREATE TRIGGER IF NOT EXISTS errors_ai AFTER INSERT ON errors BEGIN
                    INSERT INTO errors_fts(rowid, question, answer, analysis, knowledge_points)
                    VALUES (new.id, new.question, new.answer, new.analysis, new.knowledge_points);
                END;
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TRIGGER IF NOT EXISTS errors_ad AFTER DELETE ON errors BEGIN
                    INSERT INTO errors_fts(errors_fts, rowid, question, answer, analysis, knowledge_points)
                    VALUES ('delete', old.id, old.question, old.answer, old.analysis, old.knowledge_points);
                END;
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TRIGGER IF NOT EXISTS errors_au AFTER UPDATE ON errors BEGIN
                    INSERT INTO errors_fts(errors_fts, rowid, question, answer, analysis, knowledge_points)
                    VALUES ('delete', old.id, old.question, old.answer, old.analysis, old.knowledge_points);
                    INSERT INTO errors_fts(rowid, question, answer, analysis, knowledge_points)
                    VALUES (new.id, new.question, new.answer, new.analysis, new.knowledge_points);
                END;
                """
            )
        )
