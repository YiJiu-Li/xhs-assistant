"""改写接口 — SSE 流式改写 + 话题标签生成"""

import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from backend.schemas.rewrite import RewriteRequest, HashtagRequest
from chains.rewrite_chain import build_rewrite_chain, build_rag_rewrite_chain, build_hashtag_chain
from rag.vectorstore import get_rag_context

router = APIRouter()


async def _stream_chain(chain, inputs: dict):
    """将 LangChain astream 输出封装为 SSE 字节流"""
    try:
        async for chunk in chain.astream(inputs):
            data = json.dumps({"type": "token", "content": chunk}, ensure_ascii=False)
            yield f"data: {data}\n\n"
        yield f"data: {json.dumps({'type': 'done', 'content': ''})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"


@router.post("/stream")
async def rewrite_stream(req: RewriteRequest):
    """SSE 流式改写接口"""
    if req.use_rag:
        rag_ctx = get_rag_context(req.content, style=req.style, top_k=3)
        chain = build_rag_rewrite_chain(req.style, model=req.model, temperature=req.temperature)
        inputs = {"rag_context": rag_ctx, "style": req.style, "content": req.content}
    else:
        chain = build_rewrite_chain(req.style, model=req.model, temperature=req.temperature)
        inputs = {"style": req.style, "content": req.content}

    return StreamingResponse(
        _stream_chain(chain, inputs),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/hashtags")
async def generate_hashtags(req: HashtagRequest):
    """生成话题标签（非流式）"""
    chain = build_hashtag_chain(model=req.model)
    result = await chain.ainvoke({"content": req.content})
    return {"hashtags": result}
