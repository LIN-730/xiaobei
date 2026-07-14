# notifications.py — 教务通知 API (P4.7)
"""
GET /api/v1/notifications — 获取通知列表（支持分类筛选）
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.database.repositories.repos import NotificationRepo
from app.auth.dependencies import get_current_user
from app.database.models import User

router = APIRouter()


@router.get("")
async def get_notifications(
    category: str = Query(None, description="通知分类: 通知/文件/消息"),
    limit: int = Query(50, ge=1, le=200, description="返回条数"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取教务通知列表"""
    repo = NotificationRepo(db, user.id)
    notifications = await repo.get_all()

    # 按分类筛选
    if category:
        notifications = [n for n in notifications if n.category == category]

    # 按日期降序排列
    notifications.sort(key=lambda n: n.date or "", reverse=True)

    # 限制条数
    notifications = notifications[:limit]

    return {
        "total": len(notifications),
        "data": [
            {
                "id": n.id,
                "category": n.category,
                "tag": n.tag,
                "title": n.title,
                "content": n.content,
                "date": n.date,
                "link": n.link,
            }
            for n in notifications
        ],
    }
