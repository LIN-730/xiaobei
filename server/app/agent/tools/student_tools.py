# tools/student_tools.py — 学生信息/学业/预警工具 (异步版, P3)
import ast
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.repositories.repos import StudentRepo, AcademicStatusRepo, AcademicWarningRepo


async def query_student_info(db: AsyncSession, user_id: str) -> str:
    """查询学生基本信息。触发: 「我的信息」「我是哪个专业」「我的学院」等。"""
    try:
        repo = StudentRepo(db, user_id)
        r = await repo.get_one()
        if not r:
            return "未查询到个人信息。"
        return (
            f"姓名：{r.name or '?'}  性别：{r.gender or '?'}  学院：{r.college or '?'}  "
            f"专业：{r.major or '?'}  班级：{r.class_name or '?'}  年级：{r.grade or '?'}  校区：{r.campus or '?'}"
        )
    except Exception as e:
        return f"查询失败：{e}"


async def query_academic_status(db: AsyncSession, user_id: str) -> str:
    """查询学业进度(GPA/学分/模块完成度)。触发: 「还差多少学分」「绩点多少」「学业进度」等。"""
    try:
        repo = AcademicStatusRepo(db, user_id)
        r = await repo.get_status()
        if not r:
            return "未查询到学业数据。"
        total = r.total_credits or 0
        earned = r.earned_credits or 0
        failed = r.failed_credits or 0
        gpa = r.average_gpa or 0
        result = f"📊 学业进度：\nGPA: {gpa}\n"
        result += f"总需学分: {total}  已获: {earned}  未通过: {failed}\n\n"
        if r.raw_data:
            try:
                mods = ast.literal_eval(r.raw_data)
                result += "各模块详情：\n"
                for m in mods:
                    status = (
                        "✅" if float(m.get("remaining", 1)) == 0
                        else ("⚠️" if float(m.get("earned", 0)) > 0 else "❌")
                    )
                    result += (
                        f"  {status} {m['name']}: "
                        f"需{m.get('required', 0)} 得{m.get('earned', 0)} 缺{m.get('remaining', 0)}\n"
                    )
            except Exception:
                pass
        return result
    except Exception as e:
        return f"查询失败：{e}"


async def query_warnings(db: AsyncSession, user_id: str) -> str:
    """查询学籍预警。触发: 「挂科」「预警」「警告」等。"""
    try:
        repo = AcademicWarningRepo(db, user_id)
        rows = await repo.get_all()
        if not rows:
            return "当前无学籍预警记录。"
        result = "学籍预警：\n"
        for r in rows:
            result += f"  [{r.warning_level or '?'}] {r.warning_type or '?'}：{r.description or '?'} ({r.create_time or '?'})\n"
        return result
    except Exception as e:
        return f"查询失败：{e}"
