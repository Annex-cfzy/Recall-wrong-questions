"""Review (复习) endpoints — M3."""
from __future__ import annotations

import json
import random
import string
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import AppException
from app.core.response import success_response
from app.models import Error, ReviewRecord
from app.schemas import ReviewStartRequest, ReviewSubmitRequest
from app.services import ai_service
from app.services.sm2_service import Sm2State, update_sm2

router = APIRouter(prefix="/api/review", tags=["review"])

# In-memory cache of generated variants for a review session (single-user MVP).
_review_cache: dict[str, list[dict]] = {}


def _gen_review_id() -> str:
    return "rev_" + datetime.now().strftime("%Y%m%d") + "_" + "".join(
        random.choices(string.digits, k=3)
    )


@router.get("/today")
def review_today(db: Session = Depends(get_db)):
    today = date.today()
    due = db.execute(
        select(Error).where(Error.next_review <= today)
    ).scalars().all()
    items = [
        {
            "error_id": e.id,
            "subject": e.subject,
            "knowledge_points": json.loads(e.knowledge_points) if e.knowledge_points else [],
            "mastery": e.mastery,
            "next_review": e.next_review.isoformat(),
            "overdue_days": (today - e.next_review).days,
        }
        for e in due
    ]
    # Weekly preview (next 7 days counts).
    weekly = []
    for i in range(7):
        d = today + timedelta(days=i)
        c = db.execute(
            select(Error).where(Error.next_review == d)
        ).scalars().all()
        weekly.append({"date": d.isoformat(), "count": len(c)})
    return success_response({"count": len(items), "items": items, "weekly_preview": weekly})


@router.post("/start")
async def start_review(payload: ReviewStartRequest, db: Session = Depends(get_db)):
    today = date.today()
    stmt = select(Error).where(Error.next_review <= today)
    if payload.subject:
        stmt = stmt.where(Error.subject == payload.subject)
    if payload.notebook_id:
        stmt = stmt.where(Error.notebook_id == payload.notebook_id)
    errors = db.execute(stmt).scalars().all()
    if not errors:
        raise AppException(5001, "当前没有需要复习的题目")

    errors = errors[: payload.count]
    questions = []
    variant_cache = []
    for idx, e in enumerate(errors):
        kps = json.loads(e.knowledge_points) if e.knowledge_points else []
        variant = await ai_service.generate_variant(
            {"question": e.question, "answer": e.answer, "knowledge_points": kps}
        )
        questions.append(
            {
                "index": idx,
                "error_id": e.id,
                "variant_question": variant.get("question", e.question),
                "knowledge_points": variant.get("knowledge_points", kps),
            }
        )
        variant_cache.append(
            {
                "error_id": e.id,
                "variant_question": variant.get("question", e.question),
                "standard_answer": variant.get("answer", e.answer or ""),
                "analysis": variant.get("analysis", ""),
            }
        )

    review_id = _gen_review_id()
    _review_cache[review_id] = variant_cache
    return success_response(
        {"review_id": review_id, "total": len(questions), "questions": questions}
    )


@router.post("/submit")
async def submit_review(payload: ReviewSubmitRequest, db: Session = Depends(get_db)):
    cache = _review_cache.get(payload.review_id)
    if not cache:
        raise AppException(5002, "复习会话已过期，请重新开始")

    by_index = {i: v for i, v in enumerate(cache)}
    results = []
    total_score = 0
    correct = wrong = skipped = 0
    mastery_total = 0

    for ans in payload.answers:
        v = by_index.get(ans.index)
        if not v:
            continue
        user_answer = (ans.user_answer or "").strip()
        if not user_answer:
            skipped += 1
            results.append(
                {
                    "index": ans.index,
                    "error_id": ans.error_id,
                    "is_correct": False,
                    "score": 0,
                    "quality": 0,
                    "ai_feedback": "未作答，已跳过。",
                    "standard_answer": v["standard_answer"],
                    "error_cause": "",
                    "sm2_updated": None,
                }
            )
            continue

        grade = await ai_service.grade_answer(
            v["variant_question"], user_answer, v["standard_answer"]
        )
        quality = int(grade.get("quality", 0))
        is_correct = bool(grade.get("is_correct", False))
        score = int(grade.get("score", 0))

        # Persist review record.
        rec = ReviewRecord(
            error_id=ans.error_id,
            variant_question=v["variant_question"],
            user_answer=user_answer,
            is_correct=is_correct,
            score=score,
            quality=quality,
            ai_feedback=grade.get("feedback", ""),
        )
        db.add(rec)

        # Apply SM-2 to the underlying error.
        err = db.get(Error, ans.error_id)
        if err:
            prev = Sm2State(
                repetition=err.repetition,
                interval_days=err.interval_days,
                ease_factor=err.ease_factor,
                mastery=err.mastery,
            )
            new_state = update_sm2(prev, quality)
            err.repetition = new_state.repetition
            err.interval_days = new_state.interval_days
            err.ease_factor = new_state.ease_factor
            err.mastery = new_state.mastery
            err.last_review = date.today()
            err.next_review = date.today() + timedelta(days=new_state.interval_days)
            mastery_total += new_state.mastery - prev.mastery

        total_score += score
        if is_correct:
            correct += 1
        else:
            wrong += 1
        results.append(
            {
                "index": ans.index,
                "error_id": ans.error_id,
                "is_correct": is_correct,
                "score": score,
                "quality": quality,
                "ai_feedback": grade.get("feedback", ""),
                "standard_answer": v["standard_answer"],
                "error_cause": err.error_cause if err else "",
                "sm2_updated": (
                    {
                        "repetition": new_state.repetition,
                        "interval_days": new_state.interval_days,
                        "ease_factor": new_state.ease_factor,
                        "mastery": new_state.mastery,
                        "next_review": (date.today() + timedelta(days=new_state.interval_days)).isoformat(),
                    }
                    if err
                    else None
                ),
            }
        )

    db.commit()
    _review_cache.pop(payload.review_id, None)

    max_score = max(len(results) * 100, 1)
    total_score_pct = round(total_score / max_score * 100)
    return success_response(
        {
            "review_id": payload.review_id,
            "total_score": total_score_pct,
            "correct_count": correct,
            "wrong_count": wrong,
            "skipped_count": skipped,
            "mastery_delta": mastery_total,
            "results": results,
        }
    )
