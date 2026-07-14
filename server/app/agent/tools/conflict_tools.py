# tools/conflict_tools.py — 课程冲突检测 (P6.3)
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.repositories.repos import CourseRepo


WEEKDAY_NAMES = {1: "周一", 2: "周二", 3: "周三", 4: "周四", 5: "周五", 6: "周六", 7: "周日"}


async def detect_course_conflicts(
    db: AsyncSession,
    user_id: str,
) -> str:
    """
    检测当前课表中的课程时间冲突（同一天同一时段重叠 + 周次重叠）。
    无参数，自动检测所有已选课程。
    触发: 「课表冲突」「有没有撞课」「时间冲突」「课程重叠」等。
    """
    try:
        repo = CourseRepo(db, user_id)
        courses = await repo.get_all()

        if not courses:
            return "没有课表数据。请先同步教务数据。"

        conflicts = []

        for i in range(len(courses)):
            for j in range(i + 1, len(courses)):
                a = courses[i]
                b = courses[j]

                # 条件1: 同一天
                if not a.week_day or not b.week_day:
                    continue
                if a.week_day != b.week_day:
                    continue

                # 条件2: 时间段重叠
                a_start = a.start_node or 0
                a_end = a.end_node or 0
                b_start = b.start_node or 0
                b_end = b.end_node or 0

                if a_start == 0 or a_end == 0 or b_start == 0 or b_end == 0:
                    continue

                if a_start > b_end or b_start > a_end:
                    continue  # 不重叠

                # 条件3: 周次重叠
                a_sw = a.start_week or 1
                a_ew = a.end_week or 20
                b_sw = b.start_week or 1
                b_ew = b.end_week or 20

                if a_sw > b_ew or b_sw > a_ew:
                    continue  # 不重叠

                # 计算重叠周次范围
                overlap_weeks = f"第{max(a_sw, b_sw)}-{min(a_ew, b_ew)}周"

                conflicts.append({
                    "course_a": a.course_name or "未知",
                    "course_b": b.course_name or "未知",
                    "weekday": a.week_day,
                    "overlap_nodes": f"第{max(a_start, b_start)}-{min(a_end, b_end)}节",
                    "overlap_weeks": overlap_weeks,
                    "detail_a": f"{a_start}-{a_end}节 第{a_sw}-{a_ew}周",
                    "detail_b": f"{b_start}-{b_end}节 第{b_sw}-{b_ew}周",
                })

        if not conflicts:
            return "✅ 当前课表没有时间冲突，所有课程安排合理。"

        result = f"🔴 检测到 {len(conflicts)} 处课程时间冲突：\n\n"
        for ix, c in enumerate(conflicts, 1):
            wd = WEEKDAY_NAMES.get(c["weekday"], f"周{c['weekday']}")
            result += (
                f"{ix}. {wd} {c['overlap_nodes']} ({c['overlap_weeks']})\n"
                f"   🔴 {c['course_a']} ({c['detail_a']})\n"
                f"   ↔️ {c['course_b']} ({c['detail_b']})\n\n"
            )

        result += "💡 建议：如有冲突课程，请及时联系教务或调整选课安排。"
        return result

    except Exception as e:
        return f"冲突检测失败：{e}"
