"""Export service — builds PDF (WeasyPrint) and Markdown for a notebook.

WeasyPrint is optional in minimal environments; when unavailable the PDF
endpoint falls back to styled HTML so a downloadable artefact is still produced
(see export.py). Markdown is generated natively with no external deps.
"""
from __future__ import annotations

from datetime import date

from app.core.exceptions import AppException
from app.models import Error, Notebook
from sqlalchemy.orm import Session


def _fetch(db: Session, notebook_id: int):
    nb = db.get(Notebook, notebook_id)
    if not nb:
        raise AppException(2001, "目标错题本不存在")
    errors = (
        db.query(Error)
        .filter(Error.notebook_id == notebook_id)
        .order_by(Error.created_at.asc())
        .all()
    )
    return nb, errors


def _esc(text: str | None) -> str:
    from html import escape

    return escape(text or "")


def _render_html(nb: Notebook, errors: list[Error], include_answer: bool = True) -> str:
    today = date.today().isoformat()
    rows: list[str] = []
    for i, e in enumerate(errors, 1):
        d = e.to_dict()
        kps = "、".join(d.get("knowledge_points") or [])
        block = f"<div class='q'><h3>第 {i} 题 · {_esc(d.get('subject'))}</h3>"
        block += (
            f"<p class='label'>题干</p><div class='area q-area'>{_esc(d.get('question'))}</div>"
        )
        if include_answer:
            if d.get("answer"):
                block += f"<p class='label'>答案</p><div class='area a-area'>{_esc(d.get('answer'))}</div>"
            if d.get("analysis"):
                block += f"<p class='label'>解析</p><div class='area a-area'>{_esc(d.get('analysis'))}</div>"
        if d.get("error_cause"):
            block += f"<p class='label'>错因</p><div class='cause'>{_esc(d.get('error_cause'))}</div>"
        if kps:
            block += f"<p class='label'>知识点</p><div class='kp'>{_esc(kps)}</div>"
        block += "</div>"
        rows.append(block)
    body = "".join(rows) if rows else "<p class='empty'>该错题本还没有错题。</p>"
    return f"""<!doctype html><html lang="zh"><head><meta charset="utf-8">
<title>{_esc(nb.name)}</title>
<style>
 @page {{ size: A4; margin: 18mm; }}
 body {{ font-family: 'PingFang SC','Microsoft YaHei',sans-serif; color:#1d1d1f; line-height:1.6; }}
 h1 {{ font-size: 22px; }}
 .meta {{ color:#6e6e73; font-size:12px; margin-bottom:16px; }}
 .q {{ border:1px solid #e5e5ea; border-radius:12px; padding:14px; margin-bottom:14px; page-break-inside: avoid; }}
 h3 {{ font-size:15px; margin:0 0 6px; }}
 .label {{ color:#6e6e73; font-size:12px; margin:10px 0 4px; }}
 .area {{ border-left:4px solid #3B82F6; padding:8px 10px; background:#f5f5f7; border-radius:6px; white-space:pre-wrap; }}
 .a-area {{ border-left-color:#10B981; }}
 .cause {{ color:#FF3B30; }}
 .kp {{ color:#007AFF; }}
 .empty {{ color:#6e6e73; }}
</style></head><body>
<h1>{_esc(nb.name)} · 错题导出</h1>
<div class="meta">学科：{_esc(nb.subject)} ｜ 共 {len(errors)} 题 ｜ 导出日期：{today}</div>
{body}
</body></html>"""


def build_markdown(nb: Notebook, errors: list[Error], include_answer: bool = True) -> str:
    today = date.today().isoformat()
    lines = [
        f"# {nb.name} · 错题导出",
        "",
        f"> 学科：{nb.subject} ｜ 共 {len(errors)} 题 ｜ 导出日期：{today}",
        "",
    ]
    if not errors:
        lines.append("_该错题本还没有错题。_")
        return "\n".join(lines)
    for i, e in enumerate(errors, 1):
        d = e.to_dict()
        lines.append(f"## 第 {i} 题（{d.get('subject') or '通用'}）")
        lines.append("")
        lines.append("**题干**")
        lines.append("")
        lines.append(f"> {d.get('question') or ''}")
        lines.append("")
        if include_answer:
            if d.get("answer"):
                lines.append("**答案**")
                lines.append("")
                lines.append(f"> {d.get('answer')}")
                lines.append("")
            if d.get("analysis"):
                lines.append("**解析**")
                lines.append("")
                lines.append(f"> {d.get('analysis')}")
                lines.append("")
        if d.get("error_cause"):
            lines.append(f"**错因**：{d.get('error_cause')}")
            lines.append("")
        kps = "、".join(d.get("knowledge_points") or [])
        if kps:
            lines.append(f"**知识点**：{kps}")
            lines.append("")
        lines.append("---")
        lines.append("")
    return "\n".join(lines)


def build_pdf_bytes(nb: Notebook, errors: list[Error], include_answer: bool = True):
    """Return PDF bytes, or None when WeasyPrint is unavailable."""
    try:
        import weasyprint  # noqa: F401
    except Exception:
        return None
    html = _render_html(nb, errors, include_answer)
    return weasyprint.HTML(string=html).write_pdf()
