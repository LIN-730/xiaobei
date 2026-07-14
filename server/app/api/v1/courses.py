# courses.py — 课表 API
import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.database.repositories.repos import CourseRepo, SelectedCourseRepo
from app.auth.dependencies import get_current_user
from app.database.models import User
from app.agent.user_profile import get_current_semester

router = APIRouter()

WEEKDAY_NAMES = {1: "周一", 2: "周二", 3: "周三", 4: "周四", 5: "周五", 6: "周六", 7: "周日"}


@router.get("")
async def get_courses(
    week_day: int = Query(None, ge=1, le=7, description="星期 (1-7)"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户课表"""
    repo = CourseRepo(db, user.id)
    if week_day is not None:
        courses = await repo.get_by_weekday(week_day)
    else:
        courses = await repo.get_all()

    return {
        "total": len(courses),
        "data": [
            {
                "course_name": c.course_name,
                "course_code": c.course_code,
                "teacher": c.teacher,
                "classroom": c.classroom,
                "week_day": c.week_day,
                "start_node": c.start_node,
                "end_node": c.end_node,
                "start_week": c.start_week,
                "end_week": c.end_week,
                "credit": c.credit,
                "course_type": c.course_type,
            }
            for c in courses
        ],
    }


@router.get("/selected")
async def get_selected_courses(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取已选课程（选课结果）"""
    repo = SelectedCourseRepo(db, user.id)
    courses = await repo.get_all()
    return {
        "total": len(courses),
        "data": [
            {
                "course_name": c.course_name,
                "course_code": c.course_code,
                "teacher": c.teacher,
                "credit": c.credit,
                "course_type": c.course_type,
                "classroom": c.classroom,
                "select_type": c.select_type,
            }
            for c in courses
        ],
    }


def _estimate_semester_start() -> datetime.date:
    """估算当前学期开学日期（近似，用于 ICS 日历）"""
    sem = get_current_semester()
    xqm = sem["xqm"]
    xnm = int(sem["xnm"])
    if xqm == "3":  # 秋季学期: 9月1日附近
        return datetime.date(xnm, 9, 1)
    elif xqm == "12":  # 春季学期: 2月底/3月初
        return datetime.date(xnm + 1, 3, 1)
    else:  # 小学期: 7月1日
        return datetime.date(xnm + 1, 7, 1)


# 北化上课时间表 (第N节 → 开始时间)
NODE_START_TIMES = {
    1: (8, 0), 2: (8, 55), 3: (9, 50), 4: (10, 45),
    5: (11, 40), 6: (14, 0), 7: (14, 55), 8: (15, 50),
    9: (16, 45), 10: (17, 40), 11: (19, 0), 12: (19, 55),
    13: (20, 50),
}
NODE_END_TIMES = {
    1: (8, 50), 2: (9, 45), 3: (10, 40), 4: (11, 35),
    5: (12, 30), 6: (14, 50), 7: (15, 45), 8: (16, 40),
    9: (17, 35), 10: (18, 30), 11: (19, 50), 12: (20, 45),
    13: (21, 20),
}


def _format_ics_datetime(d: datetime.date, t: tuple) -> str:
    """格式化为 ICS 本地时间: YYYYMMDDTHHMMSS"""
    return d.strftime("%Y%m%d") + f"T{t[0]:02d}{t[1]:02d}00"


def _generate_ics(courses: list, sem_start: datetime.date) -> str:
    """从课表数据生成 ICS 日历字符串"""
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//buct-edu-assistant//CN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:北化课表",
    ]

    for c in courses:
        if not c.week_day or not c.start_node or not c.end_node:
            continue
        if not c.start_week:
            continue

        # 计算第一次上课日期
        # sem_start 是开学日期，假设是周一
        # 实际开学日可能是任意星期，需要调整
        sem_start_wd = sem_start.weekday()  # 0=周一, 6=周日
        course_wd = (c.week_day - 1) % 7  # 转为 0=周一

        days_offset = course_wd - sem_start_wd
        if days_offset < 0:
            days_offset += 7
        days_offset += (c.start_week - 1) * 7

        first_date = sem_start + datetime.timedelta(days=days_offset)

        # 最后一次上课日期
        end_week = c.end_week or c.start_week
        last_offset = course_wd - sem_start_wd
        if last_offset < 0:
            last_offset += 7
        last_offset += (end_week - 1) * 7
        last_date = sem_start + datetime.timedelta(days=last_offset)

        # 上课时间
        start_time = NODE_START_TIMES.get(c.start_node, (8, 0))
        end_time = NODE_END_TIMES.get(c.end_node, (9, 50))

        dtstart = _format_ics_datetime(first_date, start_time)
        dtend = _format_ics_datetime(first_date, end_time)
        until = last_date.strftime("%Y%m%d") + "T235959Z"

        summary = c.course_name or "课程"
        location = c.classroom or ""
        description = f"教师: {c.teacher or '未知'} | 第{c.start_week}-{end_week}周 | {c.course_type or ''}"

        lines.append("BEGIN:VEVENT")
        lines.append(f"DTSTART:{dtstart}")
        lines.append(f"DTEND:{dtend}")
        lines.append(f"RRULE:FREQ=WEEKLY;UNTIL={until}")
        lines.append(f"SUMMARY:{summary}")
        if location:
            lines.append(f"LOCATION:{location}")
        lines.append(f"DESCRIPTION:{description}")
        lines.append("END:VEVENT")

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


@router.get("/export/ics")
async def export_course_ics(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """导出课表为 ICS 日历文件（可导入 Apple/Google/Outlook 日历）"""
    repo = CourseRepo(db, user.id)
    courses = await repo.get_all()

    if not courses:
        return Response(
            content="BEGIN:VCALENDAR\r\nVERSION:2.0\r\nEND:VCALENDAR\r\n",
            media_type="text/calendar",
            headers={"Content-Disposition": "attachment; filename=buct_courses.ics"},
        )

    sem_start = _estimate_semester_start()
    ics_content = _generate_ics(courses, sem_start)

    return Response(
        content=ics_content,
        media_type="text/calendar; charset=utf-8",
        headers={
            "Content-Disposition": "attachment; filename=buct_courses.ics",
            "Cache-Control": "no-cache",
        },
    )


@router.get("/conflicts")
async def detect_course_conflicts(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """检测课表时间冲突（同一天时段重叠 + 周次重叠）"""
    repo = CourseRepo(db, user.id)
    courses = await repo.get_all()

    conflicts = []

    for i in range(len(courses)):
        for j in range(i + 1, len(courses)):
            a = courses[i]
            b = courses[j]

            if not a.week_day or not b.week_day or a.week_day != b.week_day:
                continue

            a_start = a.start_node or 0
            a_end = a.end_node or 0
            b_start = b.start_node or 0
            b_end = b.end_node or 0

            if a_start == 0 or b_start == 0:
                continue
            if a_start > b_end or b_start > a_end:
                continue

            a_sw = a.start_week or 1
            a_ew = a.end_week or 20
            b_sw = b.start_week or 1
            b_ew = b.end_week or 20

            if a_sw > b_ew or b_sw > a_ew:
                continue

            conflicts.append({
                "course_a": {
                    "course_name": a.course_name,
                    "course_code": a.course_code,
                    "teacher": a.teacher,
                    "classroom": a.classroom,
                    "week_day": a.week_day,
                    "start_node": a.start_node,
                    "end_node": a.end_node,
                    "start_week": a.start_week,
                    "end_week": a.end_week,
                },
                "course_b": {
                    "course_name": b.course_name,
                    "course_code": b.course_code,
                    "teacher": b.teacher,
                    "classroom": b.classroom,
                    "week_day": b.week_day,
                    "start_node": b.start_node,
                    "end_node": b.end_node,
                    "start_week": b.start_week,
                    "end_week": b.end_week,
                },
                "weekday_name": WEEKDAY_NAMES.get(a.week_day, f"周{a.week_day}"),
                "overlap_nodes": f"第{max(a_start, b_start)}-{min(a_end, b_end)}节",
                "overlap_weeks": f"第{max(a_sw, b_sw)}-{min(a_ew, b_ew)}周",
            })

    return {
        "total": len(conflicts),
        "has_conflicts": len(conflicts) > 0,
        "data": conflicts,
    }
