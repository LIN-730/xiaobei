# classrooms.py — 空闲教室 API (P4.6)
"""
GET /api/v1/classrooms — 查询空闲教室
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.database.repositories.repos import ClassroomRepo
from app.auth.dependencies import get_current_user
from app.database.models import User

router = APIRouter()


@router.get("")
async def get_classrooms(
    week_day: int = Query(None, ge=1, le=7, description="星期 (1-7)"),
    building: str = Query(None, description="教学楼名 (可选模糊)"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取空闲教室列表"""
    repo = ClassroomRepo(db, user.id)
    if week_day is not None:
        classrooms = await repo.get_by_weekday(week_day, building)
    else:
        classrooms = await repo.get_all()

    if building and week_day is None:
        # 非索引筛选：内存过滤
        classrooms = [c for c in classrooms
                      if building in (c.building or "")]

    return {
        "total": len(classrooms),
        "data": [
            {
                "campus": c.campus,
                "building": c.building,
                "room_no": c.room_no,
                "capacity": c.capacity,
                "week_day": c.week_day,
                "start_node": c.start_node,
                "end_node": c.end_node,
                "status": c.status,
            }
            for c in classrooms
        ],
    }
