"""Dashboard (数据看板) endpoints — M4."""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import success_response
from app.models import Error, ReviewRecord

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/trends")
def dashboard_trends(days: int = 30, db: Session = Depends(get_db)):
    today = date.today()
    start = today - timedelta(days=days - 1)

    errors = db.execute(select(Error)).scalars().all()
    reviews = db.execute(select(ReviewRecord)).scalars().all()

    # Input trend by created_at date.
    input_counter: Counter = Counter()
    for e in errors:
        if e.created_at and e.created_at.date() >= start:
            input_counter[e.created_at.date().isoformat()] += 1

    # Review trend by reviewed_at date.
    review_counter: Counter = Counter()
    correct_counter: Counter = Counter()
    for r in reviews:
        if r.reviewed_at and r.reviewed_at.date() >= start:
            review_counter[r.reviewed_at.date().isoformat()] += 1
            if r.is_correct:
                correct_counter[r.reviewed_at.date().isoformat()] += 1

    dates = [(start + timedelta(days=i)).isoformat() for i in range(days)]
    input_trend = [{"date": d, "count": input_counter.get(d, 0)} for d in dates]
    review_trend = [
        {
            "date": d,
            "count": review_counter.get(d, 0),
            "correct": correct_counter.get(d, 0),
        }
        for d in dates
    ]

    # Mastery distribution.
    mastered = sum(1 for e in errors if e.mastery >= 80)
    reviewing = sum(1 for e in errors if 50 <= e.mastery < 80)
    unstarted = sum(1 for e in errors if e.mastery < 50)

    # Subject distribution.
    subj_counter: Counter = Counter()
    for e in errors:
        subj_counter[e.subject] += 1
    subject_distribution = [
        {"subject": s, "count": c} for s, c in subj_counter.most_common()
    ]

    # Mastery trend (avg mastery per day based on errors created that day as proxy).
    mastery_by_date: dict[str, list[int]] = defaultdict(list)
    for e in errors:
        if e.created_at and e.created_at.date() >= start:
            mastery_by_date[e.created_at.date().isoformat()].append(e.mastery)
    mastery_trend = [
        {
            "date": d,
            "avg_mastery": round(sum(mastery_by_date[d]) / len(mastery_by_date[d]), 1)
            if mastery_by_date.get(d)
            else 0,
        }
        for d in dates
    ]

    avg_mastery = round(sum(e.mastery for e in errors) / len(errors), 1) if errors else 0
    review_accuracy = round(
        sum(1 for r in reviews if r.is_correct) / len(reviews), 2
    ) if reviews else 0

    return success_response(
        {
            "summary": {
                "total_errors": len(errors),
                "total_reviews": len(reviews),
                "avg_mastery": avg_mastery,
                "review_accuracy": review_accuracy,
            },
            "input_trend": input_trend,
            "review_trend": review_trend,
            "mastery_distribution": {
                "mastered": mastered,
                "reviewing": reviewing,
                "unstarted": unstarted,
            },
            "subject_distribution": subject_distribution,
            "mastery_trend": mastery_trend,
        }
    )


@router.get("/knowledge-graph")
def knowledge_graph(db: Session = Depends(get_db)):
    errors = db.execute(select(Error)).scalars().all()

    kp_stats: dict[str, dict] = {}
    cooccur: Counter = Counter()
    for e in errors:
        kps = json.loads(e.knowledge_points) if e.knowledge_points else []
        subject = e.subject
        for kp in kps:
            if kp not in kp_stats:
                kp_stats[kp] = {"count": 0, "mastery_sum": 0, "subject": subject}
            kp_stats[kp]["count"] += 1
            kp_stats[kp]["mastery_sum"] += e.mastery
            kp_stats[kp]["subject"] = subject
        # Co-occurrence edges.
        for i in range(len(kps)):
            for j in range(i + 1, len(kps)):
                key = tuple(sorted((kps[i], kps[j])))
                cooccur[key] += 1

    def color_for(m: float) -> str:
        if m >= 80:
            return "#34C759"
        if m >= 50:
            return "#FF9500"
        return "#FF3B30"

    nodes = []
    for kp, st in kp_stats.items():
        avg_m = round(st["mastery_sum"] / st["count"], 1) if st["count"] else 0
        nodes.append(
            {
                "id": f"kp_{abs(hash(kp))}",
                "label": kp,
                "subject": st["subject"],
                "error_count": st["count"],
                "mastery": avg_m,
                "color": color_for(avg_m),
            }
        )
    # Map label -> id for edges.
    label_to_id = {n["label"]: n["id"] for n in nodes}
    edges = []
    for (a, b), w in cooccur.items():
        if a in label_to_id and b in label_to_id:
            edges.append(
                {"source": label_to_id[a], "target": label_to_id[b], "relation": "关联"}
            )

    return success_response({"nodes": nodes, "edges": edges})
