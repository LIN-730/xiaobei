# exams.py — 考试安排 API
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.database.repositories.repos import ExamRepo
from app.auth.dependencies import get_current_user
from app.database.models import User

router = APIRouter()


@router.get("")
async def get_exams(
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取考试安排"""
    repo = ExamRepo(db, user.id)
    exams = await repo.get_upcoming(limit=limit)

    return {
        "total": len(exams),
        "data": [
            {
                "course_name": e.course_name,
                "exam_date": e.exam_date,
                "exam_time": e.exam_time,
                "classroom": e.classroom,
                "seat_no": e.seat_no,
                "exam_type": e.exam_type,
                "campus": e.campus,
            }
            for e in exams
        ],
    }
