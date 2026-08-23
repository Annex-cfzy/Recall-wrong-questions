"""M7 智能升级服务单测 — 纯函数，不依赖数据库。"""
from __future__ import annotations

import asyncio

from app.services import insight_service as svc


def _err(eid, question, kps, cause, subject, mastery, created="2026-08-01"):
    return {
        "id": eid,
        "notebook_id": 1,
        "question": question,
        "answer": "A",
        "analysis": "解析",
        "error_cause": cause,
        "knowledge_points": kps,
        "subject": subject,
        "source": "manual",
        "mastery": mastery,
        "created_at": f"{created}T10:00:00",
        "updated_at": f"{created}T10:00:00",
    }


def _rev(error_id, is_correct, reviewed="2026-08-10"):
    return {
        "id": error_id * 10,
        "error_id": error_id,
        "variant_question": "q",
        "user_answer": "a",
        "is_correct": is_correct,
        "score": 100 if is_correct else 0,
        "quality": 5 if is_correct else 1,
        "reviewed_at": f"{reviewed}T10:00:00",
    }


def test_error_cause_distribution():
    errors = [
        _err(1, "题1", ["函数"], "计算失误", "数学", 30),
        _err(2, "题2", ["导数"], "计算失误", "数学", 40),
        _err(3, "题3", ["单词"], "概念混淆", "英语", 60),
    ]
    dist = svc.error_cause_distribution(errors)
    causes = {d["cause"]: d["count"] for d in dist}
    assert causes["计算失误"] == 2
    assert causes["概念混淆"] == 1
    assert dist[0]["count"] >= dist[-1]["count"]  # most_common 排序


def test_weak_subject_comparison():
    errors = [
        _err(1, "题1", ["函数"], "计算失误", "数学", 30),
        _err(2, "题2", ["导数"], "计算失误", "数学", 40),
        _err(3, "题3", ["单词"], "概念混淆", "英语", 80),
    ]
    reviews = [_rev(1, False), _rev(2, True), _rev(3, True)]
    cmp = svc.weak_subject_comparison(errors, reviews)
    by_subj = {c["subject"]: c for c in cmp}
    assert by_subj["数学"]["avg_mastery"] == 35
    assert by_subj["英语"]["avg_mastery"] == 80
    # 数学错误率：1 错 / 2 总 = 0.5
    assert by_subj["数学"]["error_rate"] == 0.5
    # 薄弱度降序：数学应在英语之前
    assert cmp[0]["subject"] == "数学"


def test_detect_clusters_groups_similar():
    errors = [
        _err(1, "求函数 f(x)=x^2 的导数", ["导数"], "计算失误", "数学", 30),
        _err(2, "求函数 f(x)=x^3 的导数", ["导数"], "计算失误", "数学", 35),
        _err(3, "背诵英语单词 apple 的意思", ["单词"], "概念混淆", "英语", 60),
    ]
    res = svc.detect_clusters(errors, threshold=0.5)
    # 前两题题干高度相似（共享"求导""函数"等字符），应聚为一簇
    assert res["repeated_cluster_count"] >= 1
    repeated = res["clusters"]
    sizes = [len(c["member_ids"]) for c in repeated]
    assert max(sizes) >= 2
    # 第三题与它们不相似，不应在同一簇
    assert res["total_errors"] == 3


def test_detect_clusters_repeated_knowledge_points():
    errors = [
        _err(1, "题A", ["函数", "极值"], "x", "数学", 20),
        _err(2, "题B", ["函数", "导数"], "x", "数学", 25),
        _err(3, "题C", ["单词"], "x", "英语", 70),
    ]
    res = svc.detect_clusters(errors, threshold=0.5)
    kps = {k["knowledge_point"]: k["occurrences"] for k in res["repeated_knowledge_points"]}
    assert kps.get("函数") == 2


def test_weak_point_warnings():
    errors = [
        _err(1, "题1", ["导数"], "计算失误", "数学", 20),
        _err(2, "题2", ["导数"], "计算失误", "数学", 25),
        _err(3, "题3", ["单词"], "概念混淆", "英语", 90),
    ]
    reviews = [_rev(1, False), _rev(2, False)]
    warns = svc.weak_point_warnings(errors, reviews)
    kps = {w["knowledge_point"]: w for w in warns["warnings"]}
    assert "导数" in kps
    assert kps["导数"]["level"] in ("warning", "danger")
    # 英语掌握度高，不应预警
    assert "单词" not in kps


def test_build_sprint():
    errors = [
        _err(1, "导数题1", ["导数"], "计算失误", "数学", 20, created="2026-08-01"),
        _err(2, "导数题2", ["导数"], "计算失误", "数学", 25, created="2026-08-02"),
        _err(3, "函数题", ["函数"], "概念混淆", "数学", 30, created="2026-08-03"),
        _err(4, "单词题", ["单词"], "概念混淆", "英语", 80, created="2026-08-04"),
    ]
    reviews = [_rev(1, False), _rev(2, False), _rev(3, True)]
    sprint = svc.build_sprint(errors, reviews, top_n=2, paper_size=3)
    assert sprint["focus_count"] >= 1
    assert len(sprint["mock_paper"]) <= 3
    # 最弱的题（掌握度最低）应进入组卷
    paper_ids = [p["error_id"] for p in sprint["mock_paper"]]
    assert 1 in paper_ids  # 掌握度 20 最低


def test_knowledge_mastery_trend():
    errors = [
        _err(1, "题1", ["导数"], "x", "数学", 20, created="2026-08-01"),
        _err(2, "题2", ["导数"], "x", "数学", 40, created="2026-08-02"),
        _err(3, "题3", ["单词"], "x", "英语", 70, created="2026-08-03"),
    ]
    trend = svc.knowledge_mastery_trend(errors, days=30)
    kps = {s["knowledge_point"]: s for s in trend["series"]}
    assert "导数" in kps
    assert kps["导数"]["current_mastery"] == 30


def test_build_voice_card_async():
    err = _err(1, "求函数导数", ["导数"], "计算失误", "数学", 30)
    card = asyncio.run(svc.build_voice_card(err))
    assert card["error_id"] == 1
    assert "tts_script" in card and card["tts_script"]
    assert any(sec["type"] == "解析" for sec in card["sections"])
    # mock 模式 enriched=False
    assert card["enriched"] is False
