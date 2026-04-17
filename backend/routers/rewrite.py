"""改写接口 — SSE 流式改写 + 话题标签生成"""

import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from backend.schemas.rewrite import RewriteRequest, HashtagRequest
from chains.rewrite_chain import build_rewrite_chain, build_hashtag_chain, rewrite_with_rag
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
        rag_ctx = get_rag_context(req.content, style=req.style, top_k=2)
        # rewrite_with_rag 是同步函数，需要改成 astream 版本
        # 这里直接构建支持 RAG 的 prompt chain
        from langchain_openai import ChatOpenAI
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser
        from templates.xhs_templates import XHS_TEMPLATES
        from config import API_BASE_URL, API_KEY

        template_info = XHS_TEMPLATES.get(req.style, XHS_TEMPLATES["种草推荐"])
        style_guide = template_info["style_guide"].strip()

        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""你是一位专业的小红书内容创作者，精通{req.style}风格的文案写作。

风格要求：
{style_guide}

以下是一些爆款文案参考案例，请从中学习写作技巧和风格：
{{rag_context}}

通用规范：
1. 标题：吸引眼球，20字以内，标题前加1-2个emoji
2. 正文：分段落，每段不超过5行，段落之间空一行
3. Emoji 使用规范：每个段落至少1个emoji，关键词前后点缀，全文总计10-20个emoji
4. 语言：口语化、接地气，多用感叹号，避免书面语
5. 字数：200-400字
6. 结尾：加3-5个互动句，如「你们有没有同款体验～」「评论告诉我！」
7. 话题标签：正文最后单独一行，输出8-10个话题标签，格式：#标签1 #标签2 …（包含2个大流量通用标签+垂直标签+长尾标签）
8. 输出格式：先输出【标题】，再输出【正文+话题标签】"""),
            ("human", "请将以下原始文案改写为小红书{style}风格：\n\n{content}"),
        ])
        llm = ChatOpenAI(
            model=req.model,
            temperature=req.temperature,
            openai_api_key=API_KEY,
            openai_api_base=API_BASE_URL,
            streaming=True,
        )
        chain = prompt | llm | StrOutputParser()
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
