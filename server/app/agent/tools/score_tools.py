# tools/score_tools.py — 成绩查询 (异步版, P3)
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.repositories.repos import ScoreRepo


async def query_scores(
    db: AsyncSession,
    user_id: str,
    term: Optional[str] = None,
    course_name: Optional[str] = None,
) -> str:
    """
    查询学生成绩。参数: term(如2025-2026-1,可选), course_name(可选,模糊)。无参数返回全部。
    触发: 「上学期成绩」「高数考了多少」「成绩」等。
    """
    try:
        repo = ScoreRepo(db, user_id)

        if term:
            rows = await repo.get_by_term(term)
        else:
            rows = await repo.get_all()

        if course_name:
            rows = [r for r in rows if course_name.lower() in (r.course_name or "").lower()]

        # 按学期倒序
        rows.sort(key=lambda r: r.term or "", reverse=True)

        if not rows:
            return "没有查询到成绩数据。请先同步数据。"

        result = "成绩信息：\n"
        for r in rows:
            gpa = f" 绩点{r.grade_point}" if r.grade_point else ""
            cred = f" {r.credit}学分" if r.credit else ""
            result += f"\n{r.term} | {r.course_name}：{r.score}分{cred}{gpa}"
        return result
    except Exception as e:
        return f"成绩查询失败：{e}"
