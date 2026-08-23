"""Error (错题) endpoints — M2."""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import AppException
from app.core.response import success_response
from app.models import Error, Notebook
from app.schemas import ErrorImportRequest, ErrorListParams, ErrorTextRequest, ErrorUpdate
from app.services import ai_service, ocr_service, vector_service

router = APIRouter(prefix="/api/errors", tags=["errors"])


def _initial_next_review() -> date:
    return date.today() + timedelta(days=1)


def _create_error(
    db: Session, question: str, answer: str, notebook_id: int, subject: str, source: str,
    image_path: str | None = None, knowledge_points: list | None = None,
    error_cause: str | None = None, analysis: str | None = None,
) -> Error:
    nb = db.get(Notebook, notebook_id)
    if not nb:
        raise AppException(2001, "目标错题本不存在")
    err = Error(
        notebook_id=notebook_id,
        question=question,
        answer=answer or None,
        analysis=analysis,
        error_cause=error_cause,
        knowledge_points=json.dumps(knowledge_points or [], ensure_ascii=False),
        subject=subject or nb.subject,
        source=source,
        image_path=image_path,
        next_review=_initial_next_review(),
    )
    db.add(err)
    db.commit()
    db.refresh(err)
    vector_service.add_vector(err.id, f"{question} {' '.join(knowledge_points or [])}")
    return err


@router.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    raw = await file.read()
    ocr_service.validate_image(file.filename or "x.bin", file.content_type or "", len(raw))
    ocr_text = await ocr_service.recognize(raw, file.filename or "x.bin")
    if not ocr_text.strip():
        raise AppException(3003, "未识别到文字内容，请重新拍照或手动输入")
    questions = await ai_service.split_questions(ocr_text)
    return success_response({"ocr_text": ocr_text, "questions": questions})


@router.post("/import")
async def import_errors(payload: ErrorImportRequest, db: Session = Depends(get_db)):
    imported = []
    for item in payload.questions:
        classified = await ai_service.classify_error(item.question, item.subject)
        err = _create_error(
            db,
            question=item.question,
            answer=item.answer,
            notebook_id=item.notebook_id,
            subject=item.subject,
            source=item.source,
            image_path=item.image_path,
            knowledge_points=classified.get("knowledge_points"),
            error_cause=classified.get("error_cause"),
        )
        imported.append(
            {
                "id": err.id,
                "question": err.question,
                "knowledge_points": classified.get("knowledge_points", []),
                "error_cause": classified.get("error_cause", ""),
                "mastery": err.mastery,
                "next_review": err.next_review.isoformat(),
            }
        )
    return success_response({"imported": imported})


@router.post("/text")
async def text_input(payload: ErrorTextRequest, db: Session = Depends(get_db)):
    classified = await ai_service.classify_error(payload.question, payload.subject)
    err = _create_error(
        db,
        question=payload.question,
        answer=payload.answer,
        notebook_id=payload.notebook_id,
        subject=payload.subject,
        source="text",
        knowledge_points=classified.get("knowledge_points"),
        error_cause=classified.get("error_cause"),
    )
    return success_response(
        {
            "id": err.id,
            "knowledge_points": classified.get("knowledge_points", []),
            "error_cause": classified.get("error_cause", ""),
            "mastery": err.mastery,
            "next_review": err.next_review.isoformat(),
        }
    )


@router.get("")
def list_errors(params: ErrorListParams = Depends(), db: Session = Depends(get_db)):
    stmt = select(Error)
    filters = []
    if params.notebook_id is not None:
        filters.append(Error.notebook_id == params.notebook_id)
    if params.subject:
        filters.append(Error.subject == params.subject)
    if params.mastery_min is not None:
        filters.append(Error.mastery >= params.mastery_min)
    if params.mastery_max is not None:
        filters.append(Error.mastery <= params.mastery_max)
    if params.is_due:
        filters.append(Error.next_review <= date.today())

    # Full-text search via FTS5 virtual table.
    if params.search:
        from sqlalchemy import text

        rows = db.execute(
            text("SELECT rowid FROM errors_fts WHERE errors_fts MATCH :q"),
            {"q": params.search},
        ).fetchall()
        ids = [r[0] for r in rows]
        filters.append(Error.id.in_(ids) if ids else Error.id == -1)

    if filters:
        stmt = stmt.where(*filters)

    total_stmt = select(Error)
    if filters:
        total_stmt = total_stmt.where(*filters)
    total = len(db.execute(total_stmt).scalars().all())

    sort_col = {
        "created_at": Error.created_at,
        "mastery": Error.mastery,
        "next_review": Error.next_review,
    }[params.sort]
    stmt = stmt.order_by(sort_col.desc() if params.order == "desc" else sort_col.asc())
    stmt = stmt.limit(params.page_size).offset((params.page - 1) * params.page_size)

    items = [e.to_dict() for e in db.execute(stmt).scalars().all()]
    return success_response(
        {
            "items": items,
            "total": total,
            "page": params.page,
            "page_size": params.page_size,
        }
    )


@router.get("/{error_id}")
def error_detail(error_id: int, db: Session = Depends(get_db)):
    err = db.get(Error, error_id)
    if not err:
        raise AppException(2002, "错题不存在")
    data = err.to_dict()
    data["review_history"] = [r.to_dict() for r in err.review_records]
    return success_response(data)


@router.put("/{error_id}")
async def update_error(error_id: int, payload: ErrorUpdate, db: Session = Depends(get_db)):
    err = db.get(Error, error_id)
    if not err:
        raise AppException(2002, "错题不存在")
    if payload.question is not None:
        err.question = payload.question
    if payload.answer is not None:
        err.answer = payload.answer
    if payload.analysis is not None:
        err.analysis = payload.analysis
    if payload.error_cause is not None:
        err.error_cause = payload.error_cause
    if payload.knowledge_points is not None:
        err.knowledge_points = json.dumps(payload.knowledge_points, ensure_ascii=False)
    if payload.notebook_id is not None:
        err.notebook_id = payload.notebook_id
    if payload.subject is not None:
        err.subject = payload.subject
    db.commit()
    # Keep vector in sync when searchable text changed.
    if payload.question is not None or payload.knowledge_points is not None:
        kps = json.loads(err.knowledge_points) if err.knowledge_points else []
        vector_service.update_vector(err.id, f"{err.question} {' '.join(kps)}")
    return success_response({"id": err.id, "vector_updated": True})


@router.delete("/{error_id}")
def delete_error(error_id: int, db: Session = Depends(get_db)):
    err = db.get(Error, error_id)
    if not err:
        raise AppException(2002, "错题不存在")
    db.delete(err)
    db.commit()
    vector_service.delete_vector(error_id)
    return success_response({"id": error_id, "vector_deleted": True})
