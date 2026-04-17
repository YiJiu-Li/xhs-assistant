"""知识库接口 — 封装 rag/vectorstore.py"""

from typing import List
from fastapi import APIRouter, HTTPException, UploadFile, File
from backend.schemas.knowledge import AddDocRequest, SearchRequest, DocItem
import rag.vectorstore as vs

router = APIRouter()

_MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB


@router.get("/stats")
async def get_stats():
    """知识库统计信息"""
    docs = vs.list_all_documents()
    styles: dict[str, int] = {}
    for d in docs:
        styles[d["style"]] = styles.get(d["style"], 0) + 1
    return {"total": len(docs), "by_style": styles}


@router.get("/list", response_model=List[DocItem])
async def list_docs():
    """列出所有文档"""
    return vs.list_all_documents()


@router.post("/add")
async def add_doc(req: AddDocRequest):
    """手动添加文案到知识库"""
    ok = vs.add_document(
        title=req.title,
        content=req.content,
        style=req.style,
        hashtags=req.hashtags,
    )
    return {"status": "ok" if ok else "error"}


@router.post("/search")
async def search_docs(req: SearchRequest):
    """相似度搜索"""
    docs = vs.search_similar(req.query, style=req.style, top_k=req.top_k)
    return {
        "results": [
            {
                "content": d.page_content,
                "style": d.metadata.get("style", ""),
                "title": d.metadata.get("title", ""),
                "hashtags": d.metadata.get("hashtags", ""),
            }
            for d in docs
        ]
    }


@router.delete("/clear")
async def clear_docs():
    """清空知识库（危险操作）"""
    vs.clear_all_documents()
    return {"status": "ok"}


@router.delete("/{doc_id}")
async def delete_doc(doc_id: str):
    """删除指定文档"""
    ok = vs.delete_document(doc_id)
    return {"status": "ok" if ok else "error"}


@router.post("/init-samples")
async def init_samples():
    """初始化内置样本"""
    vs.init_vectorstore_with_samples()
    return {"status": "ok"}
