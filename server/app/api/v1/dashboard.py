# dashboard.py — 仪表盘聚合 API
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.database.repositories.repos import (
    CourseRepo, ScoreRepo, ExamRepo, StudentRepo,
    AcademicStatusRepo, AcademicWarningRepo,
)
from app.auth.dependencies import get_current_user
from app.database.models import User

router = APIRouter()


@router.get("")
async def get_dashboard(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取仪表盘聚合数据"""
    # 并行获取各项数据
    course_count = await CourseRepo(db, user.id).count()
    score_stats = await ScoreRepo(db, user.id).get_gpa_stats()
    exam_count = await ExamRepo(db, user.id).count()
    student = await StudentRepo(db, user.id).get_one()
    status = await AcademicStatusRepo(db, user.id).get_status()
    warning_count = await AcademicWarningRepo(db, user.id).count()

    return {
        "student": {
            "name": student.name if student else None,
            "college": student.college if student else None,
            "major": student.major if student else None,
            "grade": student.grade if student else None,
        },
        "kpi": {
            "course_count": course_count,
            "exam_count": exam_count,
            "total_credits": score_stats["total_credits"],
            "avg_gpa": score_stats["avg_gpa"],
            "warning_count": warning_count,
        },
        "academic_status": {
            "total_credits": status.total_credits if status else 0,
            "earned_credits": status.earned_credits if status else 0,
            "average_gpa": status.average_gpa if status else 0,
            "required_done": status.required_done if status else 0,
            "required_total": status.required_total if status else 0,
        } if status else None,
    }
