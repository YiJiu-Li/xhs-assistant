"""批量处理 Chain — 并发处理多条文案"""

import asyncio
from typing import Generator
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from config import API_BASE_URL, API_KEY, FAST_MODEL, DEFAULT_TEMPERATURE, BATCH_MAX_SIZE
from chains.rewrite_chain import build_rewrite_chain, build_hashtag_chain


def process_batch(
    texts: list[str],
    style: str,
    model: str = FAST_MODEL,
    generate_tags: bool = True,
) -> Generator[dict, None, None]:
    """
    批量改写文案，逐条 yield 结果供 Streamlit 实时展示

    Yields:
        dict: {"index": int, "original": str, "rewritten": str, "hashtags": str, "status": "ok"|"error", "error": str}
    """
    if len(texts) > BATCH_MAX_SIZE:
        texts = texts[:BATCH_MAX_SIZE]

    rewrite_chain = build_rewrite_chain(style, model=model, temperature=DEFAULT_TEMPERATURE)
    hashtag_chain = build_hashtag_chain(model=model) if generate_tags else None

    for idx, text in enumerate(texts):
        text = text.strip()
        if not text:
            continue
        try:
            rewritten = rewrite_chain.invoke({"style": style, "content": text})
            hashtags = ""
            if hashtag_chain:
                hashtags = hashtag_chain.invoke({"content": rewritten})
            yield {
                "index": idx + 1,
                "original": text,
                "rewritten": rewritten,
                "hashtags": hashtags,
                "status": "ok",
                "error": "",
            }
        except Exception as e:
            yield {
                "index": idx + 1,
                "original": text,
                "rewritten": "",
                "hashtags": "",
                "status": "error",
                "error": str(e),
            }
