# app/knowledge/vectordb.py — ChromaDB向量存储与检索（多租户版）
import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime


class VectorStore:
    """
    ChromaDB向量存储封装（多租户版）。
    每个用户独立 collection，collection 名为 "edu_docs_{user_id}"。
    每个文档分块存储为 (id, text, metadata, embedding)。
    """

    def __init__(self, user_id: str = "default", persist_dir: str = None):
        self.user_id = user_id
        self.persist_dir = persist_dir or os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "..", "chroma_db"
        )
        self._client = None
        self._collection = None

    # ── 连接 ──────────────────────────────────────────────────

    @property
    def client(self):
        if self._client is None:
            import chromadb
            os.makedirs(self.persist_dir, exist_ok=True)
            self._client = chromadb.PersistentClient(path=self.persist_dir)
        return self._client

    @property
    def collection(self):
        if self._collection is None:
            collection_name = f"edu_docs_{self.user_id}"
            try:
                self._collection = self.client.get_collection(collection_name)
            except Exception:
                self._collection = self.client.create_collection(
                    name=collection_name,
                    metadata={"description": f"教务知识库文档 - 用户{self.user_id}"}
                )
        return self._collection

    # ── 增删查 ────────────────────────────────────────────────

    def add_document(self, filename: str, chunks: List[Dict],
                     metadata: Dict = None) -> int:
        """
        将一个文档的所有分块写入向量库。

        Args:
            filename: 文件名（作为source）
            chunks: [{"id": str, "text": str, "index": int}, ...]
            metadata: 全局元数据（分类、标签等）

        Returns:
            写入的块数
        """
        if not chunks:
            return 0

        ids = [c["id"] for c in chunks]
        texts = [c["text"] for c in chunks]
        metas = []
        for c in chunks:
            m = {
                "source": filename,
                "chunk_index": c.get("index", 0),
                "total_chunks": len(chunks),
            }
            if metadata:
                m.update(metadata)
            metas.append(m)

        self.collection.delete(where={"source": filename})
        self.collection.add(ids=ids, documents=texts, metadatas=metas)
        return len(chunks)

    def search(self, query: str, top_k: int = 5,
               where: Dict = None) -> List[Dict]:
        """
        语义检索最相关的文档块。

        Returns:
            [{"text": str, "source": str, "distance": float, ...}, ...]
        """
        results = self.collection.query(
            query_texts=[query], n_results=top_k, where=where)
        items = []
        if results["ids"] and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                items.append({
                    "id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "source": results["metadatas"][0][i].get("source", ""),
                    "category": results["metadatas"][0][i].get("category", ""),
                    "distance": results["distances"][0][i] if results.get("distances") else 0,
                })
        return items

    def search_by_keyword(self, keyword: str, top_k: int = 5) -> List[Dict]:
        """关键词搜索（遍历metadata）"""
        try:
            results = self.collection.get(
                where_document={"$contains": keyword},
                limit=top_k,
            )
            items = []
            if results["ids"]:
                for i in range(len(results["ids"])):
                    items.append({
                        "id": results["ids"][i],
                        "text": results["documents"][i],
                        "source": results["metadatas"][i].get("source", ""),
                    })
            return items
        except Exception:
            return []  # ChromaDB关键词搜索可能不支持

    def list_sources(self) -> List[Dict]:
        """列出已索引的文档"""
        results = self.collection.get()
        sources = {}
        if results["metadatas"]:
            for m in results["metadatas"]:
                src = m.get("source", "unknown")
                if src not in sources:
                    sources[src] = {"source": src, "category": m.get("category", ""), "chunks": 0}
                sources[src]["chunks"] += 1
        return list(sources.values())

    def delete_source(self, filename: str) -> bool:
        """删除某文件的所有块"""
        self.collection.delete(where={"source": filename})
        return True

    def count(self) -> int:
        """总块数"""
        return self.collection.count()
