"""RAG 知识库 — 基于 ChromaDB 的爆款文案向量存储"""

import json
import os
from pathlib import Path
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from config import CHROMA_DB_PATH, COLLECTION_NAME

# 单例缓存 — 模型和向量库只在进程启动时加载一次（470MB，低功耗设备关键优化）
_embeddings: HuggingFaceEmbeddings | None = None
_vectorstore: Chroma | None = None


def get_embeddings() -> HuggingFaceEmbeddings:
    """获取 Embedding 模型单例（首次调用时加载，后续复用）"""
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
    return _embeddings


def get_vectorstore() -> Chroma:
    """获取向量数据库单例"""
    global _vectorstore
    if _vectorstore is None:
        os.makedirs(CHROMA_DB_PATH, exist_ok=True)
        _vectorstore = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=get_embeddings(),
            persist_directory=CHROMA_DB_PATH,
        )
    return _vectorstore


def load_sample_docs() -> list[Document]:
    """加载内置爆款文案样本"""
    samples_path = Path(__file__).parent / "sample_docs" / "samples.json"
    with open(samples_path, "r", encoding="utf-8") as f:
        samples = json.load(f)

    docs = []
    for item in samples:
        content = f"【标题】{item['title']}\n\n{item['content']}"
        doc = Document(
            page_content=content,
            metadata={
                "id": str(item["id"]),
                "style": item["style"],
                "title": item["title"],
                "hashtags": item.get("hashtags", ""),
                "source": "内置样本",
            },
        )
        docs.append(doc)
    return docs


def init_vectorstore_with_samples() -> Chroma:
    """初始化向量库并加载内置样本（首次调用时执行）"""
    vs = get_vectorstore()
    # 检查是否已有数据
    existing = vs.get()
    if not existing["ids"]:
        docs = load_sample_docs()
        vs.add_documents(docs)
    return vs


def add_document(
    title: str, content: str, style: str, hashtags: str = "", source: str = "用户添加"
) -> bool:
    """向知识库添加新文案"""
    vs = get_vectorstore()
    full_content = f"【标题】{title}\n\n{content}"
    doc = Document(
        page_content=full_content,
        metadata={
            "style": style,
            "title": title,
            "hashtags": hashtags,
            "source": source,
        },
    )
    vs.add_documents([doc])
    invalidate_search_cache()
    return True


_search_cache: dict[tuple, list[Document]] = {}
_CACHE_MAX = 200  # 最多缓存 200 条查询（32GB 内存充裕，可适当放大）


def search_similar(query: str, style: str = None, top_k: int = 3) -> list[Document]:
    """相似度搜索爆款文案参考（带内存缓存，相同查询直接返回）"""
    cache_key = (query.strip(), style, top_k)
    if cache_key in _search_cache:
        return _search_cache[cache_key]

    vs = get_vectorstore()
    if style:
        results = vs.similarity_search(query, k=top_k, filter={"style": style})
        if len(results) < top_k:
            extra = vs.similarity_search(query, k=top_k - len(results))
            existing_ids = {d.metadata.get("id", d.page_content[:20]) for d in results}
            for d in extra:
                d_id = d.metadata.get("id", d.page_content[:20])
                if d_id not in existing_ids:
                    results.append(d)
    else:
        results = vs.similarity_search(query, k=top_k)

    if len(_search_cache) >= _CACHE_MAX:
        # 简单淘汰：清掉最早的一半
        keys = list(_search_cache.keys())
        for k in keys[: _CACHE_MAX // 2]:
            del _search_cache[k]
    _search_cache[cache_key] = results
    return results


def invalidate_search_cache() -> None:
    """知识库内容变更后清除搜索缓存"""
    _search_cache.clear()


def get_rag_context(query: str, style: str = None, top_k: int = 2) -> str:
    """获取 RAG 上下文字符串（用于注入 Prompt）"""
    docs = search_similar(query, style=style, top_k=top_k)
    if not docs:
        return ""
    parts = []
    for i, doc in enumerate(docs, 1):
        parts.append(f"参考案例 {i}：\n{doc.page_content}")
    return "\n\n".join(parts)


def list_all_documents() -> list[dict]:
    """列出知识库中所有文档元数据"""
    vs = get_vectorstore()
    result = vs.get()
    docs = []
    for i, doc_id in enumerate(result["ids"]):
        meta = result["metadatas"][i] if result["metadatas"] else {}
        content = result["documents"][i] if result["documents"] else ""
        docs.append(
            {
                "id": doc_id,
                "title": meta.get("title", "未知"),
                "style": meta.get("style", "未知"),
                "source": meta.get("source", "未知"),
                "hashtags": meta.get("hashtags", ""),
                "content_preview": (
                    content[:80] + "..." if len(content) > 80 else content
                ),
            }
        )
    return docs


def delete_document(doc_id: str) -> bool:
    """从知识库删除指定文档"""
    vs = get_vectorstore()
    vs.delete([doc_id])
    invalidate_search_cache()
    return True


def clear_all_documents() -> bool:
    """清空整个知识库（危险操作）"""
    vs = get_vectorstore()
    result = vs.get()
    if result["ids"]:
        vs.delete(result["ids"])
    invalidate_search_cache()
    return True
