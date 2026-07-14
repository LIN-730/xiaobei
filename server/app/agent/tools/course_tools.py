# tools/course_tools.py — 课表查询 (异步版, P3)
"""将 SQLite Tool 重构为 Repository + async 模式"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.repositories.repos import CourseRepo
from app.agent.user_profile import get_current_semester

WEEK_MAP = {1: "周一", 2: "周二", 3: "周三", 4: "周四", 5: "周五", 6: "周六", 7: "周日"}


async def query_courses(
    db: AsyncSession,
    user_id: str,
    week_day: Optional[int] = None,
    course_name: Optional[str] = None,
) -> str:
    """
    查询学生课表。参数: week_day(1-7可选), course_name(可选,模糊)。
    无参数默认返回当前学期本周课表。
    触发: 「周一有什么课」「高数在哪个教室」「这周课表」等。
    """
    repo = CourseRepo(db, user_id)
    sem = get_current_semester()

    if week_day:
        rows = await repo.get_by_weekday(week_day)
    else:
        rows = await repo.get_all()

    # 默认过滤当前学期: Course 表按 user_id 隔离，且同步时只存当前学期
    # 对跨学期数据，依赖前端/Agent 按 xnm/xqm 过滤 (当前 Course 表没有 xnm/xqm)
    if course_name:
        rows = [r for r in rows if course_name.lower() in (r.course_name or "").lower()]

    if not rows:
        return f"{sem['term_name']} 没有课表数据。请先同步数据。"

    current_week = sem["week"]
    this_week = [r for r in rows if (r.start_week or 0) <= current_week <= (r.end_week or 20)]

    target = this_week if (not week_day and not course_name) else rows
    wk_label = f"第{current_week}周" if target == this_week else ""

    if not target:
        return f"📅 {sem['term_name']} 第{current_week}周无课（共{len(rows)}门）"

    return f"📅 {sem['term_name']} {wk_label}课表：\n" + _format_rows(target[:20])


def _format_rows(rows) -> str:
    result = ""
    for r in rows:
        wd = WEEK_MAP.get(r.week_day, "?") if r.week_day else "?"
        result += f"\n{wd} 第{r.start_node}-{r.end_node}节 {r.course_name}"
        result += f"\n  {r.teacher or ''} | {r.classroom or ''} | {r.course_type or ''} {r.credit}学分 | 第{r.start_week}-{r.end_week}周\n"
    return result
