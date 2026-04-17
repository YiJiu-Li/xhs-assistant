"""对话优化接口 — SQLChatMessageHistory + SSE 流式多轮对话"""

import json
import os
import sqlite3
import uuid
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from backend.db.session_store import get_session_history, _DB_PATH, create_session_record
from backend.schemas.conversation import (
    CreateSessionResponse,
    MessageRequest,
    HistoryResponse,
    MessageRecord,
    SessionListResponse,
    SessionInfo,
)
from chains.conversation_chain import build_conversation_chain

router = APIRouter()


@router.get("", response_model=SessionListResponse)
async def list_sessions():
    """列出所有对话 session"""
    if not os.path.exists(_DB_PATH):
        return SessionListResponse(sessions=[])
    try:
        conn = sqlite3.connect(_DB_PATH)
        cursor = conn.execute("""
            SELECT m.session_id,
                   COUNT(*) as cnt,
                   COALESCE(s.created_at, '') as created_at
            FROM message_store m
            LEFT JOIN sessions s ON m.session_id = s.session_id
            GROUP BY m.session_id
            ORDER BY MIN(m.id) DESC
        """)
        sessions = [
            SessionInfo(session_id=row[0], message_count=row[1], created_at=row[2])
            for row in cursor.fetchall()
        ]
        conn.close()
    except Exception:
        sessions = []
    return SessionListResponse(sessions=sessions)


@router.post("", response_model=CreateSessionResponse)
async def create_session():
    """创建新的对话 session，返回 session_id"""
    session_id = str(uuid.uuid4())
    # 初始化历史对象（触发建表）
    get_session_history(session_id)
    # 记录创建时间
    create_session_record(session_id)
    return CreateSessionResponse(session_id=session_id)


@router.get("/{session_id}", response_model=HistoryResponse)
async def get_history(session_id: str):
    """获取对话历史"""
    history = get_session_history(session_id)
    messages = history.messages
    records = []
    for msg in messages:
        role = "human" if msg.type == "human" else "ai"
        records.append(MessageRecord(role=role, content=msg.content))
    return HistoryResponse(session_id=session_id, messages=records)


@router.delete("/{session_id}")
async def clear_session(session_id: str):
    """清空对话历史"""
    history = get_session_history(session_id)
    history.clear()
    return {"status": "ok", "session_id": session_id}


@router.post("/{session_id}/message")
async def send_message(session_id: str, req: MessageRequest):
    """SSE 流式发送消息，返回 AI 回复"""
    # 同步加载历史（避免 aiosqlite 异步冲突）
    history = get_session_history(session_id)
    past_messages = history.messages  # 同步读取，sqlite:/// 驱动无问题

    chain = build_conversation_chain(model=req.model)

    async def _generate():
        ai_content = ""
        try:
            # 直接向 chain 注入历史，不使用 RunnableWithMessageHistory（避免 async 驱动冲突）
            async for chunk in chain.astream(
                {"input": req.message, "history": past_messages},
            ):
                ai_content += chunk
                data = json.dumps({"type": "token", "content": chunk}, ensure_ascii=False)
                yield f"data: {data}\n\n"
            # 流式完成后同步写回历史
            history.add_user_message(req.message)
            history.add_ai_message(ai_content)
            yield f"data: {json.dumps({'type': 'done', 'content': ''})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(
        _generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
