"""Notebook (错题本) CRUD endpoints — M1."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import AppException
from app.core.response import error_response, success_response
from app.models import Error, Notebook
from app.schemas import NotebookCreate, NotebookResponse, NotebookUpdate

router = APIRouter(prefix="/api/notebooks", tags=["notebooks"])


@router.get("")
def list_notebooks(db: Session = Depends(get_db)):
    notebooks = db.scalars(select(Notebook).order_by(Notebook.updated_at.desc())).all()
    # Count errors per notebook in a single query.
    counts = db.execute(
        select(Error.notebook_id, func.count(Error.id)).group_by(Error.notebook_id)
    ).all()
    count_map = {nb_id: c for nb_id, c in counts}
    items = [n.to_dict(error_count=count_map.get(n.id, 0)) for n in notebooks]
    return success_response({"items": items})


@router.post("")
def create_notebook(payload: NotebookCreate, db: Session = Depends(get_db)):
    nb = Notebook(name=payload.name, subject=payload.subject, color=payload.color)
    db.add(nb)
    db.commit()
    db.refresh(nb)
    return success_response(nb.to_dict())


@router.put("/{notebook_id}")
def update_notebook(
    notebook_id: int, payload: NotebookUpdate, db: Session = Depends(get_db)
):
    nb = db.get(Notebook, notebook_id)
    if not nb:
        raise AppException(2001, "错题本不存在")
    if payload.name is not None:
        nb.name = payload.name
    if payload.subject is not None:
        nb.subject = payload.subject
    if payload.color is not None:
        nb.color = payload.color
    db.commit()
    return success_response({"id": nb.id})


@router.delete("/{notebook_id}")
def delete_notebook(notebook_id: int, db: Session = Depends(get_db)):
    nb = db.get(Notebook, notebook_id)
    if not nb:
        raise AppException(2001, "错题本不存在")
    deleted_errors = (
        db.execute(
            select(func.count(Error.id)).where(Error.notebook_id == notebook_id)
        ).scalar()
        or 0
    )
    # Cascade deletes errors + their FTS rows + vectors handled in service layer.
    from app.services.vector_service import delete_notebook_vectors

    db.delete(nb)
    db.commit()
    try:
        delete_notebook_vectors(notebook_id)
    except Exception:
        pass  # vector store is best-effort
    return success_response(
        {"id": notebook_id, "deleted_errors": deleted_errors, "deleted_vectors": deleted_errors}
    )
