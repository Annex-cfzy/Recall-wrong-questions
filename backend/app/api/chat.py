"""Chat (AI 对话) endpoints — M4.

Streaming uses SSE: events are JSON objects sent as `data: {..}\n\n`.
"""
from __future__ import annotations

import json
from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import AppException
from app.core.response import success_response
from app.models import ChatMessage, ChatSession, Error, Notebook
from app.schemas import ChatSaveRequest, ChatSessionCreate, ChatStreamRequest
from app.services import ai_service

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/sessions")
def create_session(payload: ChatSessionCreate, db: Session = Depends(get_db)):
    s = ChatSession(title=payload.title)
    db.add(s)
    db.commit()
    db.refresh(s)
    return success_response(s.to_dict())


@router.get("/sessions")
def list_sessions(db: Session = Depends(get_db)):
    sessions = db.scalars(
        select(ChatSession).order_by(ChatSession.updated_at.desc())
    ).all()
    items = []
    for s in sessions:
        last = db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == s.id)
            .order_by(ChatMessage.id.desc())
            .limit(1)
        ).scalar_one_or_none()
        items.append(s.to_dict(last_message_preview=last.content[:40] if last else ""))
    return success_response({"items": items})


@router.get("/sessions/{session_id}/messages")
def get_messages(session_id: int, db: Session = Depends(get_db)):
    msgs = db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.id.asc())
    ).scalars().all()
    return success_response({"messages": [m.to_dict() for m in msgs]})


@router.delete("/sessions/{session_id}")
def delete_session(session_id: int, db: Session = Depends(get_db)):
    s = db.get(ChatSession, session_id)
    if not s:
        raise AppException(2003, "对话不存在")
    db.delete(s)
    db.commit()
    return success_response({"id": session_id})


@router.post("/stream")
async def chat_stream(payload: ChatStreamRequest, db: Session = Depends(get_db)):
    session = db.get(ChatSession, payload.session_id)
    if not session:
        raise AppException(2003, "对话不存在")

    # Persist user message.
    user_msg = ChatMessage(session_id=session.id, role="user", content=payload.message)
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    assistant_msg = ChatMessage(session_id=session.id, role="assistant", content="")
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    async def event_gen():
        yield f"data: {json.dumps({'type': 'start', 'message_id': assistant_msg.id}, ensure_ascii=False)}\n\n"
        collected = []
        try:
            async for chunk in ai_service.stream_chat(payload.message):
                collected.append(chunk)
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)}\n\n"
            full = "".join(collected)
            assistant_msg.content = full
            session.updated_at = datetime.now()
            db.commit()
            yield f"data: {json.dumps({'type': 'done', 'message_id': assistant_msg.id, 'content': full}, ensure_ascii=False)}\n\n"
        except Exception:
            yield f"data: {json.dumps({'type': 'error', 'code': 4001, 'message': 'AI 服务暂时不可用'}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_gen(), media_type="text/event-stream")


@router.post("/save-to-errors")
async def save_to_errors(payload: ChatSaveRequest, db: Session = Depends(get_db)):
    msg = db.get(ChatMessage, payload.message_id)
    if not msg:
        raise AppException(2004, "消息不存在")
    session = db.get(ChatSession, msg.session_id)
    # Use the preceding user question as the question, assistant reply as analysis.
    user_q = (
        db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == msg.session_id, ChatMessage.role == "user")
            .order_by(ChatMessage.id.desc())
        ).scalar_one_or_none()
    )
    question = user_q.content if user_q else msg.content
    nb = db.get(Notebook, payload.notebook_id)
    if not nb:
        raise AppException(2001, "目标错题本不存在")
    err = Error(
        notebook_id=payload.notebook_id,
        question=question,
        analysis=msg.content,
        subject=payload.subject or nb.subject,
        source="chat",
        next_review=__import__("datetime").date.today()
        + __import__("datetime").timedelta(days=1),
    )
    db.add(err)
    db.commit()
    db.refresh(err)
    return success_response(
        {"error_id": err.id, "knowledge_points": [], "error_cause": ""}
    )
