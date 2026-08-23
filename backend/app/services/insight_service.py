"""智能升级分析服务 — M7.

纯函数实现，全部从已有的 Error / ReviewRecord 数据聚合得出，不依赖任何
外部 API（mock 优先）。这样在断网、无 Key 的情况下整套升级功能都能跑：
  - 知识点掌握趋势（knowledge_mastery_trend）
  - 错因分布（error_cause_distribution）
  - 薄弱学科对比（weak_subject_comparison）
  - 相似错题聚类（detect_clusters）
  - 薄弱点预警（weak_point_warnings）
  - 考前冲刺清单 + 模拟组卷（build_sprint）
  - 语音讲解卡文本生成（build_voice_card，mock 优先，真实模式可接 DeepSeek）

所有函数接收「dict 列表」（由 ORM.to_dict() 转换而来），便于脱离数据库单测。
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from typing import Any

# --- 阈值（可调） ---
DEFAULT_MASTERY_THRESHOLD = 50  # 掌握度低于该值视为薄弱
DEFAULT_ERROR_RATE_THRESHOLD = 0.5  # 错误率高于该值预警
SPIKE_WINDOW_DAYS = 7  # 突增对比的最近窗口


# --------------------------------------------------------------------------
# 工具
# --------------------------------------------------------------------------
def _parse_kp(raw: Any) -> list[str]:
    if isinstance(raw, list):
        return [str(x) for x in raw]
    if not raw:
        return []
    try:
        data = json.loads(raw)
        return [str(x) for x in data] if isinstance(data, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


def _tokens(text: str | None) -> set[str]:
    """字符级分词（兼容中文，无需 jieba），用于相似度计算。"""
    if not text:
        return set()
    return set(re.findall(r"[\w\u4e00-\u9fff]", text))


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    union = a | b
    return len(a & b) / len(union) if union else 0.0


def _as_date(value: Any) -> date | None:
    if isinstance(value, (datetime, date)):
        return value.date() if isinstance(value, datetime) else value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value).date()
        except ValueError:
            return None
    return None


# --------------------------------------------------------------------------
# 1. 知识点掌握趋势
# --------------------------------------------------------------------------
def knowledge_mastery_trend(
    errors: list[dict], days: int = 30
) -> dict:
    """返回每个知识点的掌握度时间序列 + 整体趋势。

    由于错题掌握度随复习变化，这里以「该题录入日期」为锚点，统计当天录入的
    该题所属知识点的平均掌握度，形成趋势线；同时给出每个知识点当前最新掌握度。
    """
    today = date.today()
    start = today - timedelta(days=days - 1)
    dates = [(start + timedelta(days=i)) for i in range(days)]
    date_strs = [d.isoformat() for d in dates]

    # kp -> {date: [mastery...]}
    kp_series: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))
    for e in errors:
        kps = _parse_kp(e.get("knowledge_points"))
        if not kps:
            kps = ["未分类"]
        d = _as_date(e.get("created_at")) or today
        for kp in kps:
            kp_series[kp][d.isoformat()].append(int(e.get("mastery", 0) or 0))
    # 计算每个知识点当前平均掌握度
    kp_avg: dict[str, float] = {}
    for e in errors:
        kps = _parse_kp(e.get("knowledge_points")) or ["未分类"]
        for kp in kps:
            kp_avg.setdefault(kp, []).append(int(e.get("mastery", 0) or 0))
    kp_current = {
        kp: round(sum(v) / len(v), 1) for kp, v in kp_avg.items()
    }

    series = []
    for kp, by_date in kp_series.items():
        points = [
            {
                "date": ds,
                "avg_mastery": round(sum(by_date.get(ds, [])) / len(by_date[ds]), 1)
                if by_date.get(ds)
                else None,
            }
            for ds in date_strs
        ]
        # 过滤掉全 None 的段
        series.append(
            {
                "knowledge_point": kp,
                "current_mastery": kp_current.get(kp, 0),
                "points": points,
            }
        )
    # 只保留有数据的知识点，按当前掌握度升序（最薄弱在前）
    series = [s for s in series if any(p["avg_mastery"] is not None for p in s["points"])]
    series.sort(key=lambda s: s["current_mastery"])

    return {
        "days": days,
        "series": series,
        "knowledge_point_count": len(series),
    }


# --------------------------------------------------------------------------
# 2. 错因分布
# --------------------------------------------------------------------------
def error_cause_distribution(errors: list[dict]) -> list[dict]:
    counter: Counter = Counter()
    for e in errors:
        cause = (e.get("error_cause") or "").strip() or "未标注"
        counter[cause] += 1
    total = sum(counter.values()) or 1
    return [
        {"cause": c, "count": n, "ratio": round(n / total, 3)}
        for c, n in counter.most_common()
    ]


# --------------------------------------------------------------------------
# 3. 薄弱学科对比
# --------------------------------------------------------------------------
def weak_subject_comparison(errors: list[dict], reviews: list[dict]) -> list[dict]:
    """每个学科：错题数、平均掌握度、复习次数、错误率、薄弱度评分。"""
    subj_errors: dict[str, list[dict]] = defaultdict(list)
    for e in errors:
        subj_errors[e.get("subject", "通用")].append(e)

    # error_id -> subject 映射，便于关联复习
    err_subject: dict[int, str] = {
        int(e["id"]): e.get("subject", "通用") for e in errors if e.get("id") is not None
    }

    subj_reviews: dict[str, list[dict]] = defaultdict(list)
    for r in reviews:
        sid = int(r["error_id"]) if r.get("error_id") is not None else None
        subj = err_subject.get(sid, "通用") if sid is not None else "通用"
        subj_reviews[subj].append(r)

    result = []
    for subj, errs in subj_errors.items():
        avg_mastery = round(
            sum(int(e.get("mastery", 0) or 0) for e in errs) / len(errs), 1
        )
        revs = subj_reviews.get(subj, [])
        wrong = sum(1 for r in revs if r.get("is_correct") is False)
        total_rev = len(revs)
        error_rate = round(wrong / total_rev, 3) if total_rev else 0.0
        # 薄弱度评分：掌握度越低、错误率越高越薄弱（0~100）
        weakness = round((100 - avg_mastery) * 0.6 + error_rate * 100 * 0.4, 1)
        result.append(
            {
                "subject": subj,
                "error_count": len(errs),
                "avg_mastery": avg_mastery,
                "review_count": total_rev,
                "error_rate": error_rate,
                "weakness": weakness,
            }
        )
    result.sort(key=lambda x: x["weakness"], reverse=True)
    return result


# --------------------------------------------------------------------------
# 4. 相似错题聚类（去重）
# --------------------------------------------------------------------------
def detect_clusters(errors: list[dict], threshold: float = 0.5) -> dict:
    """贪心聚类：两题共享≥1 知识点，或题干字符 Jaccard≥threshold 则归为同簇。

    仅做「识别与分组」，不删除/合并任何已有数据（符合“不修改现有成果”）。
    返回 clusters（含代表性题目、成员、共享知识点）与反复错的知识点提示。
    """
    items = [e for e in errors if e.get("id") is not None]
    clusters: list[dict] = []

    for e in items:
        e_tokens = _tokens(e.get("question", ""))
        e_kps = set(_parse_kp(e.get("knowledge_points")))
        placed = False
        for cl in clusters:
            rep_question = cl["representative_question"]
            rep_tokens = _tokens(rep_question)
            rep_kps = set(cl["shared_knowledge_points"])
            share_kp = len(e_kps & rep_kps) > 0
            sim = _jaccard(e_tokens, rep_tokens)
            if share_kp or sim >= threshold:
                cl["member_ids"].append(int(e["id"]))
                cl["members"].append(
                    {
                        "id": int(e["id"]),
                        "question": e.get("question", ""),
                        "subject": e.get("subject", "通用"),
                        "mastery": int(e.get("mastery", 0) or 0),
                    }
                )
                cl["shared_knowledge_points"] = sorted(
                    set(cl["shared_knowledge_points"]) | e_kps
                )
                placed = True
                break
        if not placed:
            clusters.append(
                {
                    "cluster_id": f"c{len(clusters) + 1}",
                    "representative_id": int(e["id"]),
                    "representative_question": e.get("question", ""),
                    "subject": e.get("subject", "通用"),
                    "shared_knowledge_points": sorted(e_kps),
                    "member_ids": [int(e["id"])],
                    "members": [
                        {
                            "id": int(e["id"]),
                            "question": e.get("question", ""),
                            "subject": e.get("subject", "通用"),
                            "mastery": int(e.get("mastery", 0) or 0),
                        }
                    ],
                }
            )

    # 仅保留多题簇（真正的“相似/重复”）
    repeated = [c for c in clusters if len(c["member_ids"]) > 1]
    repeated.sort(key=lambda c: len(c["member_ids"]), reverse=True)

    # 反复错的知识点：出现在多个错题里且平均掌握度低
    kp_mastery: dict[str, list[int]] = defaultdict(list)
    for e in items:
        for kp in _parse_kp(e.get("knowledge_points")):
            kp_mastery[kp].append(int(e.get("mastery", 0) or 0))
    repeated_kps = [
        {
            "knowledge_point": kp,
            "occurrences": len(m),
            "avg_mastery": round(sum(m) / len(m), 1),
        }
        for kp, m in kp_mastery.items()
        if len(m) >= 2
    ]
    repeated_kps.sort(key=lambda x: (x["avg_mastery"], -x["occurrences"]))

    return {
        "threshold": threshold,
        "total_errors": len(items),
        "cluster_count": len(clusters),
        "repeated_cluster_count": len(repeated),
        "clusters": repeated,
        "repeated_knowledge_points": repeated_kps,
    }


# --------------------------------------------------------------------------
# 5. 薄弱点预警
# --------------------------------------------------------------------------
def weak_point_warnings(
    errors: list[dict],
    reviews: list[dict],
    mastery_threshold: int = DEFAULT_MASTERY_THRESHOLD,
    error_rate_threshold: float = DEFAULT_ERROR_RATE_THRESHOLD,
) -> dict:
    """对每个知识点计算：当前平均掌握度、近期错误率、是否突增，给出预警列表。"""
    items = [e for e in errors if e.get("id") is not None]
    kp_errors: dict[str, list[dict]] = defaultdict(list)
    for e in items:
        for kp in _parse_kp(e.get("knowledge_points")) or ["未分类"]:
            kp_errors[kp].append(e)

    err_subject_date: dict[int, tuple[str, date | None]] = {}
    for e in items:
        err_subject_date[int(e["id"])] = (
            e.get("subject", "通用"),
            _as_date(e.get("created_at")),
        )

    # 复习按 error_id 归并，统计各知识点错误率
    kp_reviews: dict[str, list[dict]] = defaultdict(list)
    for r in reviews:
        sid = int(r["error_id"]) if r.get("error_id") is not None else None
        if sid is None or sid not in err_subject_date:
            continue
        for kp in _parse_kp(
            next(
                (x.get("knowledge_points") for x in items if int(x["id"]) == sid),
                None,
            )
        ) or ["未分类"]:
            kp_reviews[kp].append(r)

    today = date.today()
    spike_start = today - timedelta(days=SPIKE_WINDOW_DAYS)
    warnings = []
    for kp, errs in kp_errors.items():
        avg_mastery = round(
            sum(int(e.get("mastery", 0) or 0) for e in errs) / len(errs), 1
        )
        revs = kp_reviews.get(kp, [])
        wrong = sum(1 for r in revs if r.get("is_correct") is False)
        total_rev = len(revs)
        error_rate = round(wrong / total_rev, 3) if total_rev else 0.0

        # 近期突增：最近 SPIKE_WINDOW_DAYS 天录入的该题量 vs 更早
        recent = [e for e in errs if (err_subject_date[int(e["id"])][1] or today) >= spike_start]
        spike = False
        if len(recent) >= 3 and len(errs) > 0:
            recent_ratio = len(recent) / len(errs)
            if recent_ratio >= 0.5:
                spike = True

        level = "ok"
        reasons: list[str] = []
        if avg_mastery < mastery_threshold:
            level = "warning"
            reasons.append(f"平均掌握度仅 {avg_mastery}%，低于 {mastery_threshold}%")
        if error_rate >= error_rate_threshold and total_rev > 0:
            level = "danger" if level == "warning" else "warning"
            reasons.append(f"复习错误率 {round(error_rate * 100)}% 偏高")
        if spike:
            level = "danger" if level != "ok" else "warning"
            reasons.append(f"近 {SPIKE_WINDOW_DAYS} 天新增 {len(recent)} 道，疑似集中出错")

        if level != "ok":
            warnings.append(
                {
                    "knowledge_point": kp,
                    "subject": errs[0].get("subject", "通用"),
                    "error_count": len(errs),
                    "avg_mastery": avg_mastery,
                    "error_rate": error_rate,
                    "recent_count": len(recent),
                    "spike": spike,
                    "level": level,
                    "reasons": reasons,
                }
            )

    level_rank = {"danger": 0, "warning": 1, "ok": 2}
    warnings.sort(key=lambda w: (level_rank.get(w["level"], 2), w["avg_mastery"]))
    return {
        "warning_count": len(warnings),
        "danger_count": sum(1 for w in warnings if w["level"] == "danger"),
        "warnings": warnings,
    }


# --------------------------------------------------------------------------
# 6. 考前冲刺清单 + 模拟组卷
# --------------------------------------------------------------------------
def build_sprint(
    errors: list[dict],
    reviews: list[dict],
    top_n: int = 10,
    paper_size: int = 10,
) -> dict:
    """基于错题数据生成：① 复习重点（最薄弱知识点）；② 模拟组卷（最弱题目）。"""
    warns = weak_point_warnings(errors, reviews)["warnings"]
    # 复习重点：预警知识点 + 掌握度最低的未掌握题知识点
    focus_kps: dict[str, dict] = {}
    for w in warns:
        focus_kps[w["knowledge_point"]] = {
            "knowledge_point": w["knowledge_point"],
            "subject": w["subject"],
            "avg_mastery": w["avg_mastery"],
            "error_rate": w["error_rate"],
            "reason": "；".join(w["reasons"]),
            "advice": _advice_for(w),
        }
    # 补充：掌握度低但还没触发预警的知识点
    kp_mastery: dict[str, list[int]] = defaultdict(list)
    kp_subj: dict[str, str] = {}
    for e in errors:
        for kp in _parse_kp(e.get("knowledge_points")) or ["未分类"]:
            kp_mastery[kp].append(int(e.get("mastery", 0) or 0))
            kp_subj[kp] = e.get("subject", "通用")
    for kp, m in kp_mastery.items():
        if kp not in focus_kps and (sum(m) / len(m)) < DEFAULT_MASTERY_THRESHOLD:
            avg = round(sum(m) / len(m), 1)
            focus_kps[kp] = {
                "knowledge_point": kp,
                "subject": kp_subj.get(kp, "通用"),
                "avg_mastery": avg,
                "error_rate": 0.0,
                "reason": f"平均掌握度 {avg}%，建议巩固",
                "advice": "安排 2~3 次间隔复习，优先做变式题。",
            }

    focus_list = sorted(
        focus_kps.values(), key=lambda x: x["avg_mastery"]
    )[:top_n]

    # 模拟组卷：掌握度最低的题目（优先未掌握），不足则补足
    weak_sorted = sorted(
        [e for e in errors if e.get("id") is not None],
        key=lambda e: int(e.get("mastery", 0) or 0),
    )
    paper_pool = weak_sorted[: max(paper_size, len(weak_sorted))]
    mock_paper = [
        {
            "index": i + 1,
            "error_id": int(e["id"]),
            "question": e.get("question", ""),
            "standard_answer": e.get("answer") or "（暂无标准答案，建议结合解析复习）",
            "knowledge_points": _parse_kp(e.get("knowledge_points")),
            "mastery": int(e.get("mastery", 0) or 0),
        }
        for i, e in enumerate(paper_pool[:paper_size])
    ]

    return {
        "focus_list": focus_list,
        "focus_count": len(focus_list),
        "mock_paper": mock_paper,
        "paper_size": len(mock_paper),
        "summary": (
            f"已为你锁定 {len(focus_list)} 个薄弱知识点，并组出 "
            f"{len(mock_paper)} 道最易错的题目用于自测。"
        ),
    }


def _advice_for(w: dict) -> str:
    if w["avg_mastery"] < 30:
        return "该知识点掌握度很低，先回归课本概念，再做基础题建立信心。"
    if w["error_rate"] >= DEFAULT_ERROR_RATE_THRESHOLD:
        return "复习时错误率偏高，放慢节奏、分步验算，重点厘清易错步骤。"
    return "保持间隔复习，尝试不看解析独立复做变式题。"


# --------------------------------------------------------------------------
# 7. 语音讲解卡
# --------------------------------------------------------------------------
async def build_voice_card(error: dict, analysis: str | None = None) -> dict:
    """将一道错题解析生成结构化讲解卡 + 可朗读文本（TTS 由前端调用浏览器合成）。

    mock 模式：用模板把题目/解析/知识点/错因组织成口播稿；
    真实模式（MOCK_EXTERNAL=false 且有 Key）：可改为调用 DeepSeek 生成更口语化讲解。
    """
    from app.core.config import settings

    question = error.get("question", "")
    answer = error.get("answer") or "（暂无标准答案）"
    ana = analysis or error.get("analysis") or "（暂无解析）"
    kps = _parse_kp(error.get("knowledge_points"))
    cause = error.get("error_cause") or "待归纳"
    subject = error.get("subject", "通用")

    if (not settings.mock_external) and settings.deepseek_api_key:
        try:
            script = await _deepseek_voice_script(error, kps, cause)
            enriched = True
        except Exception:
            script = _mock_voice_script(subject, question, kps, cause, ana, answer)
            enriched = False
    else:
        script = _mock_voice_script(subject, question, kps, cause, ana, answer)
        enriched = False

    sections = [
        {"type": "题目", "text": question},
        {"type": "考查知识点", "text": "、".join(kps) if kps else "未分类"},
        {"type": "常见错因", "text": cause},
        {"type": "解析", "text": ana},
        {"type": "标准答案", "text": answer},
    ]
    return {
        "error_id": int(error["id"]) if error.get("id") is not None else None,
        "subject": subject,
        "title": f"{subject} · {'、'.join(kps) if kps else '错题'} 讲解",
        "sections": sections,
        "tts_script": script,
        "enriched": enriched,
    }


def _mock_voice_script(subject, question, kps, cause, ana, answer) -> str:
    kp_text = "、".join(kps) if kps else "相关知识点"
    return (
        f"我们来复习一道{subject}错题。这道题考查的是{kp_text}。\n"
        f"题目是：{question}\n"
        f"你之前的常见错因是：{cause}。\n"
        f"下面看解析：{ana}\n"
        f"标准答案是：{answer}\n"
        f"建议先理解思路，再合上讲解独立做一遍，巩固这个知识点。"
    )


async def _deepseek_voice_script(error: dict, kps: list[str], cause: str) -> str:
    import httpx

    from app.core.config import settings

    prompt = (
        "你是一位老师，请用口语化、适合听的方式讲解下面这道错题，"
        "控制在 200 字以内，分'题目、知识点、错因、解析、答案'五部分口播稿。\n"
        f"题目：{error.get('question')}\n"
        f"知识点：{kps}\n错因：{cause}\n"
        f"解析：{error.get('analysis')}\n答案：{error.get('answer')}"
    )
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{settings.deepseek_base_url}/chat/completions",
            headers={"Authorization": f"Bearer {settings.deepseek_api_key}"},
            json={
                "model": settings.deepseek_model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.4,
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
