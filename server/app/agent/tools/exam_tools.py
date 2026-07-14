# tools/exam_tools.py — 考试查询 (异步版, P3)
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.repositories.repos import ExamRepo
from app.agent.user_profile import get_current_semester


async def query_exams(
    db: AsyncSession,
    user_id: str,
    course_name: Optional[str] = None,
) -> str:
    """
    查询考试安排。无参数返回当前学期考试。
    触发: 「什么时候考试」「期末」「考试」等。
    """
    try:
        sem = get_current_semester()
        repo = ExamRepo(db, user_id)
        rows = await repo.get_all()

        if course_name:
            rows = [r for r in rows if course_name.lower() in (r.course_name or "").lower()]

        if not rows:
            return f"未查询到考试安排（{sem['term_name']}）。可能尚未公布或数据未同步。"

        # 过滤当前学期 (ExamDate 格式: 2026-01-15(10:30-12:30))
        current_year = int(sem["xnm"])
        filtered = [
            r for r in rows
            if r.exam_date and (str(current_year) in str(r.exam_date) or str(current_year + 1) in str(r.exam_date))
        ]

        result = f"考试安排（{sem['term_name']}）：\n"
        for r in (filtered or rows)[:15]:
            result += f"\n{r.course_name}  {r.exam_date}  {r.classroom or ''}  座位{r.seat_no or '?'}  {r.exam_type or ''}"
        return result
    except Exception as e:
        return f"考试查询失败：{e}"
