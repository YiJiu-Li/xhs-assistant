"""批量处理接口 — SSE 逐条推送结果 + 进度事件"""

import json
import asyncio
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from backend.schemas.batch import BatchRequest
from chains.rewrite_chain import build_rewrite_chain, build_hashtag_chain
from config import BATCH_MAX_SIZE

router = APIRouter()


@router.post("/stream")
async def batch_stream(req: BatchRequest):
    """SSE 批量改写，逐条推送进度和结果"""
    texts = [t.strip() for t in req.texts if t.strip()]
    texts = texts[:BATCH_MAX_SIZE]
    total = len(texts)

    async def _generate():
        rewrite_chain = build_rewrite_chain(req.style, model=req.model)
        hashtag_chain = build_hashtag_chain(model=req.model) if req.generate_tags else None

        for idx, text in enumerate(texts):
            # 推送进度
            progress = json.dumps(
                {"type": "progress", "current": idx, "total": total}, ensure_ascii=False
            )
            yield f"data: {progress}\n\n"

            try:
                rewritten = await rewrite_chain.ainvoke({"style": req.style, "content": text})
                hashtags = ""
                if hashtag_chain:
                    hashtags = await hashtag_chain.ainvoke({"content": rewritten})

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

        # 完成信号
        done = json.dumps({"type": "done", "current": total, "total": total})
        yield f"data: {done}\n\n"

    return StreamingResponse(
        _generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
