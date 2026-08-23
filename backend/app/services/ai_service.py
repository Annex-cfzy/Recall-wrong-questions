"""AI service — DeepSeek classification / variant / grading.

When MOCK_EXTERNAL is enabled (or no API key) we fall back to deterministic
local heuristics so the MVP runs fully offline. Swap in the real DeepSeek
calls by setting MOCK_EXTERNAL=false + DEEPSEEK_API_KEY in .env.
"""
from __future__ import annotations

import json
import re
from typing import Any

from app.core.config import settings

# --- Subject keyword hints for the local mock classifier ---
_SUBJECT_HINTS = {
    "数学": ["函数", "导数", "积分", "极限", "方程", "矩阵", "向量", "概率", "数列", "几何", "三角", "极值"],
    "英语": ["单词", "语法", "阅读", "时态", "从句", "词汇", "translation", "阅读", "完形"],
    "物理": ["力", "速度", "加速度", "电场", "磁场", "能量", "牛顿", "电路", "光", "波"],
    "化学": ["反应", "元素", "分子", "离子", "酸碱", "氧化还原", "化学键", "溶液"],
    "生物": ["细胞", "基因", "DNA", "蛋白质", "酶", "光合作用", "进化"],
    "语文": ["文言文", "诗词", "阅读", "作文", "修辞", "病句"],
    "政治": ["矛盾", "价值", "马克思主义", "哲学", "经济", "法治"],
    "历史": ["朝代", "战争", "革命", "改革", "史记", "资本主义"],
}

_ERROR_CAUSE_HINTS = [
    ("概念混淆", ["混淆", "概念", "误解", "记错"]),
    ("计算失误", ["算错", "计算", "粗心", "符号", "漏项"]),
    ("审题遗漏", ["没看清", "漏看", "忽略", "条件", "审题"]),
    ("公式记错", ["公式", "定理", "记错", "用错"]),
]


async def classify_error(question: str, subject: str | None = None) -> dict:
    """Return {"knowledge_points": [...], "error_cause": "..."}."""
    if not settings.mock_external and settings.deepseek_api_key:
        prompt = (
            f"你是一位资深{subject or '学科'}教师。请对以下题目分类：\n"
            "1. 识别知识点（返回数组，如 [\"导数\", \"极值\"]）\n"
            "2. 推测可能的错因（如 \"概念混淆\"、\"计算失误\"、\"审题遗漏\"）\n\n"
            f"题目：{question}\n\n"
            '请返回 JSON 格式：{"knowledge_points": [...], "error_cause": "..."}'
        )
        try:
            raw = await _deepseek_json(prompt)
            data = json.loads(raw)
            return {
                "knowledge_points": data.get("knowledge_points", []),
                "error_cause": data.get("error_cause", ""),
            }
        except Exception:
            pass
    return _mock_classify(question, subject)


async def split_questions(ocr_text: str) -> list[dict]:
    """Split OCR text into multiple questions; each item is {"index", "question", "selected": True}."""
    if not settings.mock_external and settings.deepseek_api_key:
        prompt = (
            "你是一个题目拆分助手。下面是一张试卷/练习题的图片识别文字，"
            "请将其拆分为独立的题目。\n"
            f"识别文字：\n{ocr_text}\n\n"
            '请返回 JSON 格式：{"questions": ["题目1", "题目2", ...]}'
        )
        try:
            raw = await _deepseek_json(prompt)
            data = json.loads(raw)
            qs = data.get("questions", [])
            return [{"index": i, "question": q, "selected": True} for i, q in enumerate(qs)]
        except Exception:
            pass
    return _mock_split(ocr_text)


async def generate_variant(error: dict) -> dict:
    """Generate a variant question from an existing error dict."""
    if not settings.mock_external and settings.deepseek_api_key:
        prompt = (
            "你是一位资深学科教师。基于以下错题生成一道变体题：\n"
            "要求：1) 考查相同知识点、难度相当或略高；2) 改变数值/情境/问法，不能直接照抄；"
            "3) 输出标准答案与解析。\n"
            f"原题题干：{error.get('question')}\n"
            f"原知识点：{error.get('knowledge_points')}\n\n"
            '返回 JSON：{"question": "...", "answer": "...", "analysis": "...", "knowledge_points": [...]}'
        )
        try:
            raw = await _deepseek_json(prompt)
            return json.loads(raw)
        except Exception:
            pass
    return _mock_variant(error)


async def grade_answer(
    variant_question: str, user_answer: str, standard_answer: str
) -> dict:
    """Grade a user answer; return {is_correct, score, quality, feedback}."""
    if not settings.mock_external and settings.deepseek_api_key:
        prompt = (
            "你是批改老师。请批改学生答案并评分（0-100）。\n"
            f"题目：{variant_question}\n"
            f"标准答案：{standard_answer}\n"
            f"学生答案：{user_answer}\n\n"
            '返回 JSON：{"is_correct": true/false, "score": 0-100, "quality": 0-5, "feedback": "..."}'
        )
        try:
            raw = await _deepseek_json(prompt)
            return json.loads(raw)
        except Exception:
            pass
    return _mock_grade(user_answer, standard_answer)


# --------------------------------------------------------------------------
# Real DeepSeek call
# --------------------------------------------------------------------------
async def _deepseek_json(prompt: str) -> str:
    import httpx

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.deepseek_base_url}/chat/completions",
            headers={"Authorization": f"Bearer {settings.deepseek_api_key}"},
            json={
                "model": settings.deepseek_model,
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"},
                "temperature": 0.3,
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


# --------------------------------------------------------------------------
# Local mock implementations
# --------------------------------------------------------------------------
def _mock_classify(question: str, subject: str | None) -> dict:
    subj = subject or _detect_subject(question)
    kps = [kw for kw in _SUBJECT_HINTS.get(subj, []) if kw in question]
    if not kps:
        kps = ["未分类"]
    # Error cause heuristic: scan for hint keywords.
    cause = "概念混淆"
    for label, hints in _ERROR_CAUSE_HINTS:
        if any(h in question for h in hints):
            cause = label
            break
    return {"knowledge_points": kps, "error_cause": cause or "概念混淆"}


def _detect_subject(text: str) -> str:
    best, best_count = "通用", 0
    for subj, hints in _SUBJECT_HINTS.items():
        count = sum(1 for h in hints if h in text)
        if count > best_count:
            best, best_count = subj, count
    return best


def _mock_split(ocr_text: str) -> list[dict]:
    # Split by numbered lines (1. 2. 3.) or blank lines.
    items = re.split(r"\n\s*\n|(?=^\s*\d+[\.、])", ocr_text.strip(), flags=re.MULTILINE)
    items = [i.strip() for i in items if i and i.strip()]
    if not items:
        items = [ocr_text.strip()] if ocr_text.strip() else []
    return [{"index": i, "question": q, "selected": True} for i, q in enumerate(items)]


def _mock_variant(error: dict) -> dict:
    q = error.get("question", "")
    # Simple numeric perturbation to create a "variant".
    numbers = re.findall(r"\d+", q)
    variant = q
    if numbers:
        import random

        n = numbers[0]
        new_n = str(int(n) + random.randint(1, 5))
        variant = q.replace(n, new_n, 1)
    return {
        "question": variant or q,
        "answer": error.get("answer") or "（示例答案，请在配置 Key 后获得真实生成）",
        "analysis": error.get("analysis") or "（示例解析）",
        "knowledge_points": error.get("knowledge_points") or [],
    }


def _mock_grade(user_answer: str, standard_answer: str) -> dict:
    ua = (user_answer or "").strip()
    sa = (standard_answer or "").strip()
    if not ua:
        return {"is_correct": False, "score": 0, "quality": 0, "feedback": "未作答"}
    if ua == sa:
        return {
            "is_correct": True,
            "score": 100,
            "quality": 5,
            "feedback": "答案正确，步骤完整。",
        }
    # Partial: contains the standard answer substring → 60.
    if sa and sa in ua:
        return {
            "is_correct": True,
            "score": 70,
            "quality": 4,
            "feedback": "答案基本正确。",
        }
    return {
        "is_correct": False,
        "score": 30,
        "quality": 1,
        "feedback": f"答案不正确，标准答案为：{sa or '请参考解析'}。",
    }


async def stream_chat(message: str, history: list[str] | None = None):
    """Yield text chunks for the assistant reply (SSE source).

    Yields strings token-by-token. In mock mode we synthesise a helpful
    answer and stream it word-by-word so the UI streaming behaviour is
    exercisable offline. In real mode we proxy DeepSeek's streaming API.
    """
    if not settings.mock_external and settings.deepseek_api_key:
        async for chunk in _deepseek_stream(message):
            yield chunk
        return

    answer = _mock_answer(message)
    # Stream by character groups to mimic token streaming.
    import re

    tokens = re.findall(r"\S+\s*", answer)
    for t in tokens:
        yield t


def _mock_answer(message: str) -> str:
    subj = _detect_subject(message)
    return (
        f"关于你的问题「{message}」，我是你的 AI 学习助手。\n\n"
        f"这是一个与{subj}相关的问题。建议的解决思路：\n"
        "1. 先明确题目考查的核心知识点；\n"
        "2. 回忆相关公式或定理；\n"
        "3. 按步骤推导，注意边界条件；\n"
        "4. 完成后验算。\n\n"
        "（配置 DeepSeek API Key 后，这里会返回针对该题目的详细讲解与示例。）"
    )


async def _deepseek_stream(message: str):
    import httpx

    async with httpx.AsyncClient(timeout=30) as client:
        async with client.stream(
            "POST",
            f"{settings.deepseek_base_url}/chat/completions",
            headers={"Authorization": f"Bearer {settings.deepseek_api_key}"},
            json={
                "model": settings.deepseek_model,
                "messages": [{"role": "user", "content": message}],
                "stream": True,
            },
        ) as resp:
            async for line in resp.aiter_lines():
                if line.startswith("data:"):
                    payload = line[5:].strip()
                    if payload == "[DONE]":
                        break
                    try:
                        import json as _json

                        data = _json.loads(payload)
                        delta = data["choices"][0]["delta"].get("content", "")
                        if delta:
                            yield delta
                    except Exception:
                        continue
