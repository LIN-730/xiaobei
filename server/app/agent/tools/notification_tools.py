# tools/notification_tools.py — 通知/文件/消息查询工具 (异步版, Repository 模式)
"""
搜索教务通知/文件/消息。
使用 NotificationRepo 而非原始 SQL，依赖 db_session + user_id。
"""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.repos import NotificationRepo


async def query_notifications(
    db: AsyncSession,
    user_id: str,
    category: Optional[str] = None,
    keyword: Optional[str] = None,
    limit: int = 20,
) -> str:
    """
    搜索教务系统通知/文件/消息。

    触发: 「最近有什么通知」「选课通知」「停课消息」「教务处的文件」等。

    Args:
        db: 异步数据库会话
        user_id: 当前用户 UUID
        category: 分类筛选（可选: "通知"/"文件"/"消息"）
        keyword: 标题或内容模糊搜索（可选）
        limit: 最大返回条数，默认 20

    Returns:
        格式化后的通知列表文本
    """
    try:
        repo = NotificationRepo(db, user_id)

        # 获取所有通知（按 user_id 自动隔离）
        rows = await repo.get_all()

        # 分类筛选
        if category:
            rows = [r for r in rows if (r.category or "").lower() == category.lower()]

        # 关键词模糊搜索（标题 + 内容）
        if keyword:
            kw = keyword.lower()
            rows = [
                r for r in rows
                if kw in (r.title or "").lower()
                or kw in (r.content or "").lower()
            ]

        # 按日期倒序、截取 limit 条
        rows.sort(key=lambda r: (r.date or ""), reverse=True)
        rows = rows[:limit]

        if not rows:
            return "没有查询到相关通知/文件/消息。请先同步主页数据。"

        lines = [f"查询到 {len(rows)} 条："]
        for r in rows:
            tag = f"[{r.tag}]" if r.tag else ""
            lines.append(f"\n{tag} [{r.category}] {r.title}")
            # 截取 content 前 200 字作为预览
            content_preview = (r.content or "")[:200]
            if content_preview:
                lines.append(f"  {content_preview}")
            if r.date:
                lines.append(f"  📅 {r.date}")
            if r.link:
                lines.append(f"  🔗 {r.link}")

        return "\n".join(lines)

    except Exception as e:
        return f"通知查询失败：{e}"
