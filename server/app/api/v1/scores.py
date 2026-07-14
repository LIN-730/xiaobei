# scores.py — 成绩 API
from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.database.repositories.repos import ScoreRepo, AcademicStatusRepo
from app.auth.dependencies import get_current_user
from app.database.models import User
from app.agent.tools.gpa_tools import score_to_gp, GP_LEVELS

router = APIRouter()


class GpaSimulateItem(BaseModel):
    name: str = Field(..., description="课程名称")
    credit: float = Field(..., gt=0, description="学分")
    score: float = Field(..., ge=0, le=100, description="预估分数(0-100)")


class GpaSimulateRequest(BaseModel):
    courses: list[GpaSimulateItem] = Field(..., min_length=1, max_length=10, description="模拟课程列表")


@router.get("")
async def get_scores(
    term: str = Query(None, description="学期，如 2024-2025-1"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户成绩"""
    repo = ScoreRepo(db, user.id)
    if term:
        scores = await repo.get_by_term(term)
    else:
        scores = await repo.get_all()

    gpa_stats = await repo.get_gpa_stats()

    return {
        "total": len(scores),
        "gpa_stats": gpa_stats,
        "data": [
            {
                "course_name": s.course_name,
                "course_code": s.course_code,
                "term": s.term,
                "score": s.score,
                "credit": s.credit,
                "grade_point": s.grade_point,
                "course_type": s.course_type,
                "exam_type": s.exam_type,
            }
            for s in scores
        ],
    }


@router.get("/terms")
async def get_score_terms(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取所有学期列表"""
    repo = ScoreRepo(db, user.id)
    terms = await repo.get_all_terms()
    return {"data": terms}


@router.get("/detail")
async def get_score_detail(
    course_name: str = Query(None, description="课程名 (可选模糊)"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取成绩明细"""
    from app.database.repositories.repos import ScoreDetailRepo
    repo = ScoreDetailRepo(db, user.id)
    if course_name:
        details = await repo.get_all()
        details = [d for d in details if course_name in (d.course_name or "")]
    else:
        details = await repo.get_all()
    return {
        "total": len(details),
        "data": [
            {
                "course_name": d.course_name,
                "course_code": d.course_code,
                "term": d.term,
                "score": d.score,
                "credit": d.credit,
                "grade_point": d.grade_point,
                "course_type": d.course_type,
                "exam_type": d.exam_type,
            }
            for d in details
        ],
    }


@router.post("/gpa-simulate")
async def gpa_simulate(
    body: GpaSimulateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """GPA 模拟器 — 输入预估课程列表，计算模拟后 GPA 及变化"""
    status_repo = AcademicStatusRepo(db, user.id)
    status = await status_repo.get_status()

    if not status:
        return {
            "current_gpa": 0.0,
            "current_credits": 0.0,
            "simulated_gpa": 0.0,
            "gpa_change": 0.0,
            "courses": [],
            "message": "暂无学业数据，请先同步教务数据。",
        }

    current_credits = float(status.earned_credits or 0)
    current_gpa_sum = float(status.gpa_sum or 0)
    current_gpa = float(status.average_gpa or 0)

    sim_courses = []
    sim_gp_sum = 0.0
    sim_credits = 0.0

    for c in body.courses:
        gp = score_to_gp(c.score)
        contribution = round(gp * c.credit, 2)
        sim_courses.append({
            "name": c.name,
            "credit": c.credit,
            "score": c.score,
            "grade_point": gp,
            "gp_contribution": contribution,
        })
        sim_gp_sum += gp * c.credit
        sim_credits += c.credit

    new_total_credits = current_credits + sim_credits
    new_gpa_sum = current_gpa_sum + sim_gp_sum
    new_gpa = round(new_gpa_sum / new_total_credits, 2) if new_total_credits > 0 else 0.0
    gpa_change = round(new_gpa - current_gpa, 2)

    # 绩点对照表（复用 Agent Tool 定义，单一来源）
    gp_table = [
        {"grade": grade, "grade_point": gp, "score_range": score_range}
        for gp, score_range, grade in GP_LEVELS
    ]

    return {
        "current_gpa": current_gpa,
        "current_credits": current_credits,
        "simulated_gpa": new_gpa,
        "gpa_change": gpa_change,
        "new_total_credits": new_total_credits,
        "courses": sim_courses,
        "gp_table": gp_table,
    }
