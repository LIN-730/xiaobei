# base.py — Repository 基类 (user_id 自动隔离 + CRUD)
import json
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, text, func
from sqlalchemy.sql import Executable


def compute_sync_hash(row: Dict[str, Any]) -> str:
    """计算行的 MD5 哈希值，用于增量变更检测"""
    data = json.dumps(row, sort_keys=True, default=str)
    return hashlib.md5(data.encode()).hexdigest()


class BaseRepository:
    """Repository 基类 — 所有查询自动附加 user_id 过滤"""

    model: Type = None  # 子类必须设置

    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id

    # ── 查询 ──────────────────────────────────

    async def get_all(self, **filters) -> List:
        """获取当前用户的所有记录，可选过滤条件"""
        stmt = select(self.model).where(self.model.user_id == self.user_id)
        for key, value in filters.items():
            col = getattr(self.model, key, None)
            if col is not None and value is not None:
                stmt = stmt.where(col == value)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_one(self, **filters) -> Optional[Any]:
        """获取单条记录"""
        records = await self.get_all(**filters)
        return records[0] if records else None

    async def count(self, **filters) -> int:
        """计数"""
        stmt = select(func.count()).select_from(self.model).where(
            self.model.user_id == self.user_id
        )
        for key, value in filters.items():
            col = getattr(self.model, key, None)
            if col is not None and value is not None:
                stmt = stmt.where(col == value)
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def exists(self, **filters) -> bool:
        """是否存在"""
        return await self.count(**filters) > 0

    # ── 批量替换 (DELETE + INSERT) ─────────────

    async def replace_all(self, records: List[Dict[str, Any]]) -> int:
        """全量替换当前用户在该表的数据 — DELETE + INSERT"""
        if not records:
            return 0

        # 删除现有数据
        await self.db.execute(
            delete(self.model).where(self.model.user_id == self.user_id)
        )

        # 批量插入
        instances = []
        for row in records:
            row["user_id"] = self.user_id
            # 计算 sync_hash（如果有 sync_hash 列）
            if hasattr(self.model, "sync_hash"):
                row["sync_hash"] = compute_sync_hash(row)
            instances.append(self.model(**row))

        self.db.add_all(instances)
        await self.db.commit()
        return len(instances)

    async def upsert_by_key(
        self, records: List[Dict[str, Any]], key_fields: List[str]
    ) -> int:
        """按唯一键 upsert — 适合增量更新"""
        count = 0
        for row in records:
            row["user_id"] = self.user_id
            filters = {k: row.get(k) for k in key_fields}
            existing = await self.get_one(**filters)
            if existing:
                for k, v in row.items():
                    setattr(existing, k, v)
                count += 1
            else:
                self.db.add(self.model(**row))
                count += 1
        await self.db.commit()
        return count
