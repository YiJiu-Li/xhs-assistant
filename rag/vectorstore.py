"""RAG 知识库 — 基于 ChromaDB 的爆款文案向量存储"""

import json
import os
from pathlib import Path
from typing import Optional, List
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from config import CHROMA_DB_PATH, COLLECTION_NAME

# 单例缓存 — 模型和向量库只在进程启动时加载一次（470MB，低功耗设备关键优化）
_embeddings: Optional[HuggingFaceEmbeddings] = None
_vectorstore: Optional[Chroma] = None


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


def load_sample_docs(user_id: str) -> List[Document]:
    """加载内置爆款文案样本，附上 user_id"""
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
                "user_id": user_id,
            },
        )
        docs.append(doc)
    return docs


def init_vectorstore_with_samples(user_id: str = "public") -> Chroma:
    """为指定用户初始化内置样本（已有则跳过）"""
    store = get_vectorstore()
    existing = store.get(where={"user_id": user_id})
    if not existing["ids"]:
        docs = load_sample_docs(user_id)
        store.add_documents(docs)
    return store


def add_document(
    title: str,
    content: str,
    style: str,
    hashtags: str = "",
    source: str = "用户添加",
    user_id: str = "public",
) -> bool:
    """向知识库添加新文案"""
    store = get_vectorstore()
    full_content = f"【标题】{title}\n\n{content}"
    doc = Document(
        page_content=full_content,
        metadata={
            "style": style,
            "title": title,
            "hashtags": hashtags,
            "source": source,
            "user_id": user_id,
        },
    )
    store.add_documents([doc])
    invalidate_search_cache()
    return True


_search_cache: dict = {}
_CACHE_MAX = 200


def search_similar(
    query: str,
    style: Optional[str] = None,
    top_k: int = 3,
    user_id: Optional[str] = None,
) -> List[Document]:
    """相似度搜索，支持按 user_id 隔离（带内存缓存）"""
    cache_key = (query.strip(), style, top_k, user_id)
    if cache_key in _search_cache:
        return _search_cache[cache_key]

    store = get_vectorstore()

    def _build_filter(extra_style: Optional[str] = None) -> Optional[dict]:
        conditions = []
        if user_id is not None:
            conditions.append({"user_id": user_id})
        if extra_style:
            conditions.append({"style": extra_style})
        if not conditions:
            return None
        if len(conditions) == 1:
            return conditions[0]
        return {"$and": conditions}

    where = _build_filter(style)
    try:
        results = store.similarity_search(query, k=top_k, filter=where)
    except Exception:
        results = store.similarity_search(query, k=top_k)

    if len(_search_cache) >= _CACHE_MAX:
        keys = list(_search_cache.keys())
        for k in keys[: _CACHE_MAX // 2]:
            del _search_cache[k]
    _search_cache[cache_key] = results
    return results


def invalidate_search_cache() -> None:
    """知识库内容变更后清除搜索缓存"""
    _search_cache.clear()


def get_rag_context(
    query: str,
    style: Optional[str] = None,
    top_k: int = 2,
    user_id: Optional[str] = None,
) -> str:
    """获取 RAG 上下文字符串（用于注入 Prompt）。游客（user_id=None）返回空字符串。"""
    if user_id is None:
        return ""
    docs = search_similar(query, style=style, top_k=top_k, user_id=user_id)
    if not docs:
        return ""
    parts = []
    for i, doc in enumerate(docs, 1):
        parts.append(f"参考案例 {i}：\n{doc.page_content}")
    return "\n\n".join(parts)


def list_all_documents(user_id: Optional[str] = None) -> List[dict]:
    """列出指定用户的所有文档"""
    store = get_vectorstore()
    result = store.get(where={"user_id": user_id} if user_id else None)
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
                "user_id": meta.get("user_id", ""),
                "content": content,
                "content_preview": (
                    content[:80] + "..." if len(content) > 80 else content
                ),
            }
        )
    return docs


def get_document(doc_id: str) -> Optional[dict]:
    """获取单个文档完整内容（含 user_id）"""
    store = get_vectorstore()
    result = store.get(ids=[doc_id])
    if not result["ids"]:
        return None
    meta = result["metadatas"][0] if result["metadatas"] else {}
    content = result["documents"][0] if result["documents"] else ""
    return {
        "id": doc_id,
        "title": meta.get("title", ""),
        "style": meta.get("style", "种草推荐"),
        "source": meta.get("source", "用户添加"),
        "hashtags": meta.get("hashtags", ""),
        "user_id": meta.get("user_id", ""),
        "content": content,
    }


def update_document(
    doc_id: str,
    title: str,
    content: str,
    style: str,
    hashtags: str = "",
    user_id: str = "public",
) -> bool:
    """更新知识库中指定文档（先删后重新嵌入以刷新向量）"""
    store = get_vectorstore()
    store.delete([doc_id])
    full_content = f"【标题】{title}\n\n{content}"
    doc = Document(
        page_content=full_content,
        metadata={
            "style": style,
            "title": title,
            "hashtags": hashtags,
            "source": "用户编辑",
            "user_id": user_id,
        },
    )
    store.add_documents([doc])
    invalidate_search_cache()
    return True


def delete_document(doc_id: str) -> bool:
    """从知识库删除指定文档"""
    store = get_vectorstore()
    store.delete([doc_id])
    invalidate_search_cache()
    return True


def clear_user_documents(user_id: str) -> bool:
    """清空指定用户的所有文档"""
    store = get_vectorstore()
    result = store.get(where={"user_id": user_id})
    if result["ids"]:
        store.delete(result["ids"])
    invalidate_search_cache()
    return True


def clear_all_documents() -> bool:
    """清空整个知识库（管理员用）"""
    store = get_vectorstore()
    result = store.get()
    if result["ids"]:
        store.delete(result["ids"])
    invalidate_search_cache()
    return True
