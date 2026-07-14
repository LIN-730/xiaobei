# tools/training_tools.py — 培养方案/选课/教室工具 (异步版, P3)
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.repositories.repos import TrainingPlanRepo, SelectedCourseRepo, ClassroomRepo


async def query_training_plan(
    db: AsyncSession,
    user_id: str,
    course_type: Optional[str] = None,
) -> str:
    """
    查询培养方案。参数: course_type(可选,"必修"/"选修")。
    触发: 「培养方案」「要修哪些课」「必修课」等。
    """
    try:
        repo = TrainingPlanRepo(db, user_id)
        rows = await repo.get_by_type(course_type)
        if not rows:
            return "未查询到培养方案数据。"
        # 按专业/年级聚合
        plans = {}
        for r in rows:
            key = f"{r.major or ''}{r.grade or ''}"
            plans.setdefault(key, []).append(r)
        result = f"培养方案（共{len(plans)}个专业/年级）：\n"
        for key, courses in list(plans.items())[:5]:
            total_cred = sum(float(c.credit or 0) for c in courses)
            result += f"\n{key} ({len(courses)}门, {total_cred}学分)\n"
            for c in courses[:8]:
                result += f"  {c.course_name} {c.credit}学分 [{c.course_type or '?'}]\n"
            if len(courses) > 8:
                result += f"  ... 还有{len(courses) - 8}门\n"
        return result
    except Exception as e:
        return f"查询失败：{e}"


async def query_selected_courses(db: AsyncSession, user_id: str) -> str:
    """查询已选课程。触发: 「选了哪些课」「选课结果」等。"""
    try:
        repo = SelectedCourseRepo(db, user_id)
        rows = await repo.get_all()
        if not rows:
            return "未查询到选课结果。"
        result = "已选课程：\n"
        for r in rows:
            result += f"  {r.course_name} ({r.course_type or '?'}) {r.teacher or ''} {r.credit or 0}学分 {r.classroom or ''}\n"
        return result
    except Exception as e:
        return f"查询失败：{e}"


async def query_classrooms(
    db: AsyncSession,
    user_id: str,
    week_day: Optional[int] = None,
    building: Optional[str] = None,
) -> str:
    """查询空闲教室。参数: week_day(可选,1-7), building(可选)。触发: 「空教室」「哪有教室」等。"""
    try:
        repo = ClassroomRepo(db, user_id)
        rows = await repo.get_by_weekday(week_day, building) if week_day else await repo.get_all()
        if building and not week_day:
            rows = [r for r in rows if building.lower() in (r.building or "").lower()]
        rows = rows[:30]
        if not rows:
            return "未查询到空闲教室。"
        result = f"空闲教室（{len(rows)}间）：\n"
        for r in rows:
            result += f"  {r.campus or ''} {r.building or ''}{r.room_no or ''} 容量{r.capacity or 0}人 周{r.week_day} {r.status or ''}\n"
        return result
    except Exception as e:
        return f"查询失败：{e}"
