# knowledge.py — 知识库 REST API (P4.6)
"""
POST   /api/v1/knowledge/upload          — 上传文件并摄入知识库
GET    /api/v1/knowledge/files           — 列出已索引文件
DELETE /api/v1/knowledge/files/{filename} — 删除文件及向量
GET    /api/v1/knowledge/stats           — 知识库统计
POST   /api/v1/knowledge/search          — 语义搜索
"""
from __future__ import annotations

import os
import tempfile
from typing import Optional
from urllib.parse import unquote

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database.models import User
from app.database.session import get_db
from app.knowledge.rag import RAGManager

router = APIRouter()

# 上传限制：20MB
MAX_UPLOAD_SIZE = 20 * 1024 * 1024


# ── Pydantic 模型 ──────────────────────────────────────────────────

class KnowledgeSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="搜索关键词")
    top_k: int = Field(5, ge=1, le=20, description="返回结果数量")
    category: Optional[str] = Field(None, description="分类过滤")


# ── 辅助 ───────────────────────────────────────────────────────────

def _get_rag(user: User) -> RAGManager:
    """为当前用户创建 RAGManager 实例"""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    upload_dir = os.path.join(base_dir, "..", "uploads")
    chroma_dir = os.path.join(base_dir, "..", "chroma_db")
    return RAGManager(user_id=str(user.id), upload_dir=upload_dir, chroma_dir=chroma_dir)


# ── 端点 ───────────────────────────────────────────────────────────

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """上传文件并摄入知识库"""
    # 校验文件类型
    allowed = {".pdf", ".docx", ".doc", ".xlsx", ".xls",
               ".pptx", ".ppt", ".txt", ".md", ".csv"}
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型: {ext}。支持: {', '.join(allowed)}",
        )

    # 校验文件大小（读入内存前检查 Content-Length）
    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"文件大小超过 {MAX_UPLOAD_SIZE // 1024 // 1024}MB 限制",
        )

    # 写入临时文件
    suffix = f"_{file.filename}" if file.filename else ""
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        rag = _get_rag(user)
        result = rag.ingest_file(tmp_path, auto_classify=True)
        if result.get("status") == "error":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=result.get("error", "文件处理失败"),
            )
        return result
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.get("/files")
async def list_files(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """列出已索引的全部文件"""
    rag = _get_rag(user)
    return {"data": rag.list_files()}


@router.delete("/files/{filename:path}")
async def delete_file(
    filename: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除文件及其向量数据"""
    decoded = unquote(filename)
    rag = _get_rag(user)
    ok = rag.delete_file(decoded)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"文件不存在或已删除: {decoded}",
        )
    return {"status": "ok", "filename": decoded}


@router.get("/stats")
async def get_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取知识库统计信息"""
    rag = _get_rag(user)
    return rag.get_stats()


@router.post("/search")
async def search_knowledge(
    body: KnowledgeSearchRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """语义搜索知识库"""
    rag = _get_rag(user)
    results = rag.retrieve(body.query, top_k=body.top_k, category=body.category)
    return {"query": body.query, "total": len(results), "results": results}
