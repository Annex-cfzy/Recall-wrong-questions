"""升级功能端点 — M7（AI 能力深化 / 数据智能洞察 / 多端多场景 / 角色扩展）。

全部为新增端点，不改动任何既有路由。所有计算基于已有的 Error / ReviewRecord
数据，mock 优先，无需外部 API 即可运行。
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import success_response
from app.core.exceptions import AppException
from app.models import Error, ReviewRecord
from app.services import insight_service

router = APIRouter(prefix="/api/upgrade", tags=["upgrade"])


def _load(errors: list[Error], reviews: list[ReviewRecord]):
    err_dicts = [e.to_dict() for e in errors]
    rev_dicts = [r.to_dict() for r in reviews]
    return err_dicts, rev_dicts


@router.get("/insights")
def insights(days: int = 30, db: Session = Depends(get_db)):
    errors = db.execute(select(Error)).scalars().all()
    reviews = db.execute(select(ReviewRecord)).scalars().all()
    err_dicts, rev_dicts = _load(errors, reviews)

    mastery_trend = insight_service.knowledge_mastery_trend(err_dicts, days)
    cause_dist = insight_service.error_cause_distribution(err_dicts)
    subject_cmp = insight_service.weak_subject_comparison(err_dicts, rev_dicts)
    warnings = insight_service.weak_point_warnings(err_dicts, rev_dicts)

    return success_response(
        {
            "mastery_trend": mastery_trend,
            "error_cause_distribution": cause_dist,
            "weak_subject_comparison": subject_cmp,
            "weak_point_warnings": warnings,
        }
    )


@router.get("/clusters")
def clusters(threshold: float = 0.5, db: Session = Depends(get_db)):
    errors = db.execute(select(Error)).scalars().all()
    err_dicts, _ = _load(errors, [])
    result = insight_service.detect_clusters(err_dicts, threshold)
    return success_response(result)


@router.get("/sprint")
def sprint(top_n: int = 10, paper_size: int = 10, db: Session = Depends(get_db)):
    errors = db.execute(select(Error)).scalars().all()
    reviews = db.execute(select(ReviewRecord)).scalars().all()
    err_dicts, rev_dicts = _load(errors, reviews)
    result = insight_service.build_sprint(err_dicts, rev_dicts, top_n, paper_size)
    return success_response(result)


@router.get("/voice-card/{error_id}")
async def voice_card(error_id: int, db: Session = Depends(get_db)):
    error = db.get(Error, error_id)
    if not error:
        raise AppException(4001, f"错题不存在：{error_id}")
    card = await insight_service.build_voice_card(error.to_dict())
    return success_response(card)
