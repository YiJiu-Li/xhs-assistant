"""批量处理接口 — SSE 逐条推送结果 + 进度事件"""

import json
import asyncio
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from backend.schemas.batch import BatchRequest
from backend.auth.deps import get_current_user
from backend.db.user_store import has_quota, add_token_usage
from backend.guards.content_scope import is_strongly_offtopic, REJECTION_MESSAGE
from chains.rewrite_chain import build_rewrite_chain, build_hashtag_chain
from config import BATCH_MAX_SIZE

router = APIRouter()


@router.post("/stream")
async def batch_stream(req: BatchRequest, user=Depends(get_current_user)):
    """SSE 批量改写，逐条推送进度和结果"""
    texts = [t.strip() for t in req.texts if t.strip()]
    texts = texts[:BATCH_MAX_SIZE]
    total = len(texts)

    async def _generate():
        rewrite_chain = build_rewrite_chain(req.style, model=req.model)
        hashtag_chain = build_hashtag_chain(model=req.model) if req.generate_tags else None
        total_tokens = 0

        for idx, text in enumerate(texts):
            # 推送进度
            progress = json.dumps(
                {"type": "progress", "current": idx, "total": total}, ensure_ascii=False
            )
            yield f"data: {progress}\n\n"

            try:
                if is_strongly_offtopic(text):
                    raise ValueError(REJECTION_MESSAGE)

                rewrite_result = await rewrite_chain.ainvoke({"style": req.style, "content": text})
                rewritten = rewrite_result.content
                # 捕获 API 返回的真实 token 用量
                if hasattr(rewrite_result, 'usage_metadata') and rewrite_result.usage_metadata:
                    total_tokens += rewrite_result.usage_metadata.get('total_tokens', 0)

                hashtags = ""
                if hashtag_chain:
                    hashtag_result = await hashtag_chain.ainvoke({"content": rewritten})
                    hashtags = hashtag_result.content

                result = json.dumps({
                    "type": "result",
                    "index": idx + 1,
                    "original": text,
                    "rewritten": rewritten,
                    "hashtags": hashtags,
                    "status": "ok",
                    "error": "",
                }, ensure_ascii=False)
            except Exception as e:
                result = json.dumps({
                    "type": "result",
                    "index": idx + 1,
                    "original": text,
                    "rewritten": "",
                    "hashtags": "",
                    "status": "error",
                    "error": str(e),
                }, ensure_ascii=False)

            yield f"data: {result}\n\n"
            # 让出事件循环，避免阻塞
            await asyncio.sleep(0)

        # 记录 token 用量
        if total_tokens > 0:
            add_token_usage(int(user["user_id"]), total_tokens)

        # 完成信号
        done_msg = json.dumps({"type": "done", "current": total, "total": total})
        yield f"data: {done_msg}\n\n"

    return StreamingResponse(
        _generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
