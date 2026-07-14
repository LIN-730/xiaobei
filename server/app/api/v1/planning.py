# planning.py — 学业规划 API (P3)
"""
GET /api/v1/planning/credit-gap        — 学分缺口分析
GET /api/v1/planning/required-courses   — 必修课检查
GET /api/v1/planning/recommend          — 选课推荐
GET /api/v1/planning/path               — 学业路径规划
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.session import get_db
from app.database.models import User, EduCredential
from app.auth.dependencies import get_current_user
from app.agent.planning_engine import PlanningEngine

router = APIRouter()


async def _get_student_no(db: AsyncSession, user_id: str) -> str:
    """获取用户学号"""
    stmt = select(EduCredential).where(EduCredential.user_id == user_id)
    result = await db.execute(stmt)
    cred = result.scalar_one_or_none()
    return cred.student_no if cred else ""


async def _get_engine(
    db: AsyncSession,
    user: User,
) -> PlanningEngine:
    """创建 PlanningEngine 实例"""
    student_no = await _get_student_no(db, user.id)
    return PlanningEngine(db, user.id, student_no)


# ═══════════════════════════════════════════════════
# GET /credit-gap — 学分缺口分析
# ═══════════════════════════════════════════════════

@router.get("/credit-gap")
async def credit_gap(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    学分缺口分析：按模块组对比已修学分 vs 要求学分。
    返回各模块的 required/earned/remaining 及缺失课程。
    """
    engine = await _get_engine(db, user)
    result = await engine.analyze_credit_gap()
    return result


# ═══════════════════════════════════════════════════
# GET /required-courses — 必修课检查
# ═══════════════════════════════════════════════════

@router.get("/required-courses")
async def required_courses(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    检查必修课完成情况：列出未修/未通过的必修课。
    """
    engine = await _get_engine(db, user)
    result = await engine.check_required_courses()
    return result


# ═══════════════════════════════════════════════════
# GET /recommend — 选课推荐
# ═══════════════════════════════════════════════════

@router.get("/recommend")
async def recommend(
    semester: Optional[str] = Query(None, description="目标学期，如 2025-2026-1"),
    limit: int = Query(10, ge=1, le=30, description="最多推荐课程数"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    基于学分缺口推荐选课。
    """
    engine = await _get_engine(db, user)
    result = await engine.recommend_courses(
        target_semester=semester,
        max_recommendations=limit,
    )
    return result


# ═══════════════════════════════════════════════════
# GET /path — 学业路径规划
# ═══════════════════════════════════════════════════

@router.get("/path")
async def path(
    credits_per_semester: float = Query(25.0, ge=10.0, le=40.0, description="每学期目标学分"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    规划剩余学期的学业路径：每学期应修哪些必修课。
    """
    engine = await _get_engine(db, user)
    result = await engine.plan_path(
        target_credits_per_semester=credits_per_semester,
    )
    return result
