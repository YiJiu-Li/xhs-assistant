"""改写接口 — SSE 流式改写 + 话题标签生成"""

import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from backend.schemas.rewrite import RewriteRequest, HashtagRequest
from backend.auth.deps import get_current_user_optional
from backend.db.user_store import has_quota, add_token_usage
from backend.guards.content_scope import is_strongly_offtopic, REJECTION_MESSAGE
from chains.rewrite_chain import build_rewrite_chain, build_rag_rewrite_chain, build_hashtag_chain
from rag.vectorstore import get_rag_context

router = APIRouter()


async def _stream_chain(chain, inputs: dict, user_id: Optional[str] = None):
    """将 LangChain astream 输出封装为 SSE 字节流，完成后记录 token 用量"""
    output = ""
    total_tokens = 0
    try:
        async for chunk in chain.astream(inputs):
            token = chunk.content if hasattr(chunk, 'content') else str(chunk)
            if token:
                output += token
                data = json.dumps({"type": "token", "content": token}, ensure_ascii=False)
                yield f"data: {data}\n\n"
            # 捕获 API 返回的真实 token 用量
            if hasattr(chunk, 'usage_metadata') and chunk.usage_metadata:
                total_tokens = chunk.usage_metadata.get('total_tokens', 0)
        # 记录 token 用量（使用 API 报告的真实数据）
        if user_id and total_tokens > 0:
            add_token_usage(int(user_id), total_tokens)
        yield f"data: {json.dumps({'type': 'done', 'content': ''})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"


@router.post("/stream")
async def rewrite_stream(
    req: RewriteRequest,
    user: Optional[dict] = Depends(get_current_user_optional),
):
    """SSE 流式改写接口。RAG 仅对登录用户开放（使用其私有知识库）。"""
    user_id = user["user_id"] if user else None

    # 配额检查（仅登录用户）
    if user_id and not has_quota(int(user_id)):
        raise HTTPException(status_code=429, detail="Token 配额已用完，请联系管理员")

    if is_strongly_offtopic(req.content):
        raise HTTPException(status_code=400, detail=REJECTION_MESSAGE)

    if req.use_rag and user_id:
        rag_ctx = get_rag_context(req.content, style=req.style, top_k=3, user_id=user_id)
        chain = build_rag_rewrite_chain(req.style, model=req.model, temperature=req.temperature)
        inputs = {"rag_context": rag_ctx, "style": req.style, "content": req.content}
    else:
        chain = build_rewrite_chain(req.style, model=req.model, temperature=req.temperature)
        inputs = {"style": req.style, "content": req.content}

    return StreamingResponse(
        _stream_chain(chain, inputs, user_id=user_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/hashtags")
async def generate_hashtags(req: HashtagRequest):
    """生成话题标签（非流式）"""
    if is_strongly_offtopic(req.content):
        raise HTTPException(status_code=400, detail=REJECTION_MESSAGE)

    chain = build_hashtag_chain(model=req.model)
    result = await chain.ainvoke({"content": req.content})
    return {"hashtags": result.content}
