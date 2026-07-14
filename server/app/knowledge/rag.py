# app/knowledge/rag.py — RAG检索增强生成（多租户版）
"""
集成文档解析 → 智能分类 → 向量存储 → 检索 → Agent注入
"""
import os
from typing import List, Dict, Optional
from app.knowledge.parser import DocumentParser
from app.knowledge.classifier import classify_by_keywords, extract_course_names
from app.knowledge.vectordb import VectorStore


class RAGManager:
    """RAG全流程管理（多租户版）"""

    def __init__(self, user_id: str = "default", upload_dir: str = None, chroma_dir: str = None):
        self.user_id = user_id
        self.parser = DocumentParser(upload_dir)
        self.vectordb = VectorStore(user_id, chroma_dir)
        self.upload_dir = upload_dir or self.parser.upload_dir

    # ── 文件摄入 ──────────────────────────────────────────────

    def ingest_file(self, file_path: str, auto_classify: bool = True) -> Dict:
        """
        摄入单个文件: 解析 → 分类 → 向量化

        Returns:
            {"status": "ok/error", "filename": str, "chunks": int, "category": str, ...}
        """
        # 1. 解析
        parsed = self.parser.parse(file_path)
        if "error" in parsed:
            return {"status": "error", "filename": parsed.get("filename", ""),
                    "error": parsed["error"]}

        # 2. 分类
        category = classify_by_keywords(parsed["full_text"], parsed["filename"])
        courses = extract_course_names(parsed["full_text"])

        # 3. 向量化
        metadata = {
            "category": category,
            "file_type": parsed["type"],
            "pages": parsed["pages"],
            "size_kb": parsed["size_kb"],
            "hash": parsed["hash"],
            "courses": ", ".join(courses),
            "ingested_at": parsed["parsed_at"],
        }
        count = self.vectordb.add_document(
            parsed["filename"], parsed["chunks"], metadata
        )

        return {
            "status": "ok",
            "filename": parsed["filename"],
            "type": parsed["type"],
            "pages": parsed["pages"],
            "chunks": count,
            "category": category,
            "courses": courses,
            "size_kb": parsed["size_kb"],
        }

    def ingest_directory(self, dir_path: str) -> List[Dict]:
        """批量摄入目录下所有文件"""
        results = []
        supported = [".pdf", ".docx", ".doc", ".xlsx", ".xls",
                     ".pptx", ".ppt", ".txt", ".md", ".csv"]
        for root, _, files in os.walk(dir_path):
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext in supported:
                    result = self.ingest_file(os.path.join(root, f))
                    results.append(result)
        return results

    # ── 检索 ──────────────────────────────────────────────────

    def retrieve(self, query: str, top_k: int = 5,
                 category: str = None) -> List[Dict]:
        """检索相关文档块"""
        where = {"category": category} if category else None
        return self.vectordb.search(query, top_k=top_k, where=where)

    def retrieve_context(self, query: str, top_k: int = 5,
                         max_tokens: int = 2000) -> str:
        """
        检索并格式化为Agent可用的上下文字符串。
        """
        results = self.retrieve(query, top_k=top_k)
        if not results:
            return ""

        context_parts = []
        total_len = 0

        for r in results:
            snippet = r["text"][:500]
            source = r.get("source", "")
            cat = r.get("category", "")
            part = f"[来源: {source} ({cat})]\n{snippet}"
            if total_len + len(part) > max_tokens:
                break
            context_parts.append(part)
            total_len += len(part)

        return "\n\n---\n\n".join(context_parts)

    # ── 状态查询 ──────────────────────────────────────────────

    def get_stats(self) -> Dict:
        """知识库统计"""
        sources = self.vectordb.list_sources()
        return {
            "total_chunks": self.vectordb.count(),
            "total_sources": len(sources),
            "sources": sources,
            "categories": self._count_categories(sources),
        }

    def _count_categories(self, sources: List[Dict]) -> Dict:
        counts = {}
        for s in sources:
            cat = s.get("category", "未分类")
            counts[cat] = counts.get(cat, 0) + 1
        return counts

    def list_files(self) -> List[Dict]:
        """列出所有文件"""
        return self.vectordb.list_sources()

    def delete_file(self, filename: str) -> bool:
        """删除文件"""
        return self.vectordb.delete_source(filename)
