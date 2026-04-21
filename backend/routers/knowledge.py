"""知识库接口 — 封装 rag/vectorstore.py（按用户隔离）"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from backend.schemas.knowledge import AddDocRequest, UpdateDocRequest, SearchRequest, DocItem
from backend.auth.deps import get_current_user
import rag.vectorstore as vs

router = APIRouter()


@router.get("/stats")
async def get_stats(user=Depends(get_current_user)):
    docs = vs.list_all_documents(user_id=user["user_id"])
    styles: dict = {}
    for d in docs:
        styles[d["style"]] = styles.get(d["style"], 0) + 1
    return {
        "total_documents": len(docs),
        "collection_name": "xhs_samples",
        "by_style": styles,
    }


@router.get("/list", response_model=List[DocItem])
async def list_docs(user=Depends(get_current_user)):
    return vs.list_all_documents(user_id=user["user_id"])


@router.post("/add")
async def add_doc(req: AddDocRequest, user=Depends(get_current_user)):
    ok = vs.add_document(
        title=req.title,
        content=req.content,
        style=req.style,
        hashtags=req.hashtags,
        user_id=user["user_id"],
    )
    return {"status": "ok" if ok else "error"}


@router.post("/search")
async def search_docs(req: SearchRequest, user=Depends(get_current_user)):
    docs = vs.search_similar(req.query, style=req.style, top_k=req.top_k, user_id=user["user_id"])
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
async def clear_docs(user=Depends(get_current_user)):
    vs.clear_user_documents(user_id=user["user_id"])
    return {"status": "ok"}


@router.get("/{doc_id}")
async def get_doc(doc_id: str, user=Depends(get_current_user)):
    doc = vs.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    if doc.get("user_id") != user["user_id"]:
        raise HTTPException(status_code=403, detail="无权访问此文档")
    return doc


@router.put("/{doc_id}")
async def update_doc(doc_id: str, req: UpdateDocRequest, user=Depends(get_current_user)):
    existing = vs.get_document(doc_id)
    if not existing:
        raise HTTPException(status_code=404, detail="文档不存在")
    if existing.get("user_id") != user["user_id"]:
        raise HTTPException(status_code=403, detail="无权修改此文档")
    ok = vs.update_document(
        doc_id=doc_id,
        title=req.title,
        content=req.content,
        style=req.style,
        hashtags=req.hashtags,
        user_id=user["user_id"],
    )
    return {"status": "ok" if ok else "error"}


@router.delete("/{doc_id}")
async def delete_doc(doc_id: str, user=Depends(get_current_user)):
    existing = vs.get_document(doc_id)
    if not existing:
        raise HTTPException(status_code=404, detail="文档不存在")
    if existing.get("user_id") != user["user_id"]:
        raise HTTPException(status_code=403, detail="无权删除此文档")
    ok = vs.delete_document(doc_id)
    return {"status": "ok" if ok else "error"}


@router.post("/init-samples")
async def init_samples(user=Depends(get_current_user)):
    """为当前用户初始化内置样本"""
    vs.init_vectorstore_with_samples(user_id=user["user_id"])
    return {"status": "ok"}
