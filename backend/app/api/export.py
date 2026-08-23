"""Export endpoints (M5): PDF + Markdown of a notebook."""
from __future__ import annotations

from datetime import date
from urllib.parse import quote

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse, PlainTextResponse, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import export_service

router = APIRouter(prefix="/api/export", tags=["export"])


def _disposition(name: str, ext: str) -> str:
    fname = f"{name}_{date.today().isoformat()}.{ext}"
    # RFC 5987: send filename* in UTF-8 for non-ASCII names (Chinese).
    return f"attachment; filename*=UTF-8''{quote(fname)}"


@router.get("/pdf/{notebook_id}")
def export_pdf(notebook_id: int, include_answer: bool = True, db: Session = Depends(get_db)):
    nb, errors = export_service._fetch(db, notebook_id)
    pdf = export_service.build_pdf_bytes(nb, errors, include_answer)
    if pdf is None:
        # WeasyPrint unavailable → return styled HTML so download still works.
        html = export_service._render_html(nb, errors, include_answer)
        return HTMLResponse(
            content=html,
            headers={"Content-Disposition": _disposition(nb.name, "html")},
        )
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": _disposition(nb.name, "pdf")},
    )


@router.get("/markdown/{notebook_id}")
def export_markdown(notebook_id: int, include_answer: bool = True, db: Session = Depends(get_db)):
    nb, errors = export_service._fetch(db, notebook_id)
    md = export_service.build_markdown(nb, errors, include_answer)
    return PlainTextResponse(
        content=md,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": _disposition(nb.name, "md")},
    )
