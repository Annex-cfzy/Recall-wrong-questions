"""M7 升级端点集成测试 — 通过 API 写入种子数据后校验新端点。"""
from __future__ import annotations

import json
from datetime import date, datetime

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.database import SessionLocal
from app.main import app
from app.models import Error, Notebook, ReviewRecord


def _seed():
    db = SessionLocal()
    try:
        # Windows 下 SQLite 文件可能被连接锁定，conftest 删文件被静默跳过，
        # 故先显式清空，确保每次种子数据从零开始（确定性）。
        for e in db.execute(select(Error)).scalars().all():
            db.delete(e)
        for r in db.execute(select(ReviewRecord)).scalars().all():
            db.delete(r)
        for n in db.execute(select(Notebook)).scalars().all():
            db.delete(n)
        db.commit()

        nb = Notebook(name="测试本", subject="数学", color="#007AFF")
        db.add(nb)
        db.commit()
        db.refresh(nb)

        e1 = Error(
            notebook_id=nb.id, question="求函数 f(x)=x^2 的导数", subject="数学",
            mastery=20, next_review=date.today(),
            knowledge_points=json.dumps(["导数"], ensure_ascii=False),
            error_cause="计算失误", analysis="对 x^2 求导得 2x", answer="2x",
        )
        e2 = Error(
            notebook_id=nb.id, question="求函数 f(x)=x^3 的导数", subject="数学",
            mastery=25, next_review=date.today(),
            knowledge_points=json.dumps(["导数"], ensure_ascii=False),
            error_cause="计算失误", analysis="对 x^3 求导得 3x^2", answer="3x^2",
        )
        e3 = Error(
            notebook_id=nb.id, question="背诵单词 apple 的意思", subject="英语",
            mastery=80, next_review=date.today(),
            knowledge_points=json.dumps(["单词"], ensure_ascii=False),
            error_cause="概念混淆", analysis="apple 意为苹果", answer="苹果",
        )
        db.add_all([e1, e2, e3])
        db.commit()
        db.refresh(e1)
        db.refresh(e2)
        db.refresh(e3)

        db.add_all([
            ReviewRecord(error_id=e1.id, variant_question="q", is_correct=False, reviewed_at=datetime.now()),
            ReviewRecord(error_id=e2.id, variant_question="q", is_correct=False, reviewed_at=datetime.now()),
        ])
        db.commit()
    finally:
        db.close()


def test_upgrade_endpoints():
    with TestClient(app) as client:
        _seed()

        # insights
        r = client.get("/api/upgrade/insights")
        assert r.status_code == 200
        body = r.json()
        assert body["code"] == 0
        data = body["data"]
        assert "mastery_trend" in data
        assert "error_cause_distribution" in data
        assert "weak_subject_comparison" in data
        assert "weak_point_warnings" in data
        assert data["weak_point_warnings"]["warning_count"] >= 1

        # clusters
        r = client.get("/api/upgrade/clusters")
        assert r.status_code == 200
        cdata = r.json()["data"]
        assert cdata["total_errors"] == 3
        # e1 与 e2 题干相似，应被聚为一簇
        assert cdata["repeated_cluster_count"] >= 1

        # sprint
        r = client.get("/api/upgrade/sprint?top_n=3&paper_size=3")
        assert r.status_code == 200
        sdata = r.json()["data"]
        assert sdata["focus_count"] >= 1
        assert len(sdata["mock_paper"]) <= 3

        # voice-card
        r = client.get("/api/upgrade/voice-card/1")
        assert r.status_code == 200
        vdata = r.json()["data"]
        assert vdata["error_id"] == 1
        assert vdata["tts_script"]


def test_voice_card_missing_error():
    with TestClient(app) as client:
        r = client.get("/api/upgrade/voice-card/999999")
        # 业务错误：code != 0（HTTP 仍为 200，遵循统一信封）
        assert r.status_code == 200
        assert r.json()["code"] != 0


def test_clusters_empty():
    # Windows 下 SQLite 文件可能被连接锁定，conftest 删文件被静默跳过，
    # 故这里先显式清空数据，确保验证“空库不崩溃”的确定性。
    db = SessionLocal()
    try:
        for e in db.execute(select(Error)).scalars().all():
            db.delete(e)
        db.commit()
    finally:
        db.close()

    with TestClient(app) as client:
        r = client.get("/api/upgrade/clusters")
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["total_errors"] == 0
        assert "clusters" in data
        assert "repeated_knowledge_points" in data
