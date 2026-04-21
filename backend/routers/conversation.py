"""对话优化接口 — SQLChatMessageHistory + SSE 流式多轮对话（按用户隔离）"""

import json
import os
import sqlite3
import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from backend.auth.deps import get_current_user
from backend.db.session_store import get_session_history, _DB_PATH, create_session_record
from backend.db.user_store import has_quota, add_token_usage
from backend.guards.content_scope import check_scope, REJECTION_MESSAGE
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
async def list_sessions(user=Depends(get_current_user)):
    """列出当前用户的所有对话 session"""
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
            WHERE s.user_id = ?
            GROUP BY m.session_id
            ORDER BY MIN(m.id) DESC
        """, (user["user_id"],))
        sessions = [
            SessionInfo(session_id=row[0], message_count=row[1], created_at=row[2])
            for row in cursor.fetchall()
        ]
        conn.close()
    except Exception:
        sessions = []
    return SessionListResponse(sessions=sessions)


@router.post("", response_model=CreateSessionResponse)
async def create_session(user=Depends(get_current_user)):
    """创建新的对话 session"""
    session_id = str(uuid.uuid4())
    get_session_history(session_id)
    create_session_record(session_id, user_id=user["user_id"])
    return CreateSessionResponse(session_id=session_id)


def _assert_session_owner(session_id: str, user_id: str):
    """验证 session 属于当前用户，否则抛 403"""
    if not os.path.exists(_DB_PATH):
        raise HTTPException(status_code=404, detail="对话不存在")
    conn = sqlite3.connect(_DB_PATH)
    row = conn.execute(
        "SELECT user_id FROM sessions WHERE session_id = ?", (session_id,)
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="对话不存在")
    if row[0] != user_id:
        raise HTTPException(status_code=403, detail="无权访问此对话")


@router.get("/{session_id}", response_model=HistoryResponse)
async def get_history(session_id: str, user=Depends(get_current_user)):
    """获取对话历史"""
    _assert_session_owner(session_id, user["user_id"])
    history = get_session_history(session_id)
    messages = history.messages
    records = []
    for msg in messages:
        role = "human" if msg.type == "human" else "ai"
        records.append(MessageRecord(role=role, content=msg.content))
    return HistoryResponse(session_id=session_id, messages=records)


@router.delete("/{session_id}")
async def clear_session(session_id: str, user=Depends(get_current_user)):
    """清空对话历史"""
    _assert_session_owner(session_id, user["user_id"])
    history = get_session_history(session_id)
    history.clear()
    return {"status": "ok", "session_id": session_id}


@router.post("/{session_id}/message")
async def send_message(session_id: str, req: MessageRequest, user=Depends(get_current_user)):
    """SSE 流式发送消息，返回 AI 回复"""
    _assert_session_owner(session_id, user["user_id"])

    # 配额检查
    if not has_quota(int(user["user_id"])):
        raise HTTPException(status_code=429, detail="Token 配额已用完，请联系管理员")

    history = get_session_history(session_id)
    past_messages = history.messages

    # 三层内容范围过滤：白名单快速放行 → 黑名单快速拒绝 → 灰区 LLM 二判
    _reject, _reason = await check_scope(req.message, has_history=len(past_messages) > 0)
    if _reject:
        raise HTTPException(status_code=400, detail=_reason)

    chain = build_conversation_chain(model=req.model)

    async def _generate():
        ai_content = ""
        total_tokens = 0
        try:
            async for chunk in chain.astream(
                {"input": req.message, "history": past_messages},
            ):
                token = chunk.content if hasattr(chunk, 'content') else str(chunk)
                if token:
                    ai_content += token
                    data = json.dumps({"type": "token", "content": token}, ensure_ascii=False)
                    yield f"data: {data}\n\n"
                # 捕获 API 返回的真实 token 用量
                if hasattr(chunk, 'usage_metadata') and chunk.usage_metadata:
                    total_tokens = chunk.usage_metadata.get('total_tokens', 0)
            history.add_user_message(req.message)
            history.add_ai_message(ai_content)
            # 记录 token 用量（使用 API 报告的真实数据）
            if total_tokens > 0:
                add_token_usage(int(user["user_id"]), total_tokens)
            yield f"data: {json.dumps({'type': 'done', 'content': ''})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(
        _generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
