# user_profile.py — 学期推算 + 时间上下文（无数据库依赖）
"""
根据系统日期自动推算当前学期(xnm/xqm)和教学周。
纯日期计算，不再依赖 SQLite UserProfile 表。
week_offset 由调用方传入或默认为 0。
"""
import datetime


def get_current_semester(week_offset: int = 0) -> dict:
    """
    根据当前日期自动推算教务系统的学年学期。
    返回: {"xnm": "2025", "xqm": "16", "term_name": "2025-2026-2", "week": 16}
    """
    today = datetime.date.today()
    year = today.year
    month = today.month

    # BUCT学期(从实际课表反推):
    #   第一学期(xqm=3): 9月-1月 (秋季)
    #   第二学期(xqm=12): 3月-6月 (春季)
    #   第三学期/小学期(xqm=16): 7月-8月 (暑假短学期)
    if month >= 9:
        xqm = "3"; academic_year_start = year
    elif month == 1:
        xqm = "3"; academic_year_start = year - 1
    elif 2 <= month <= 6:
        xqm = "12"; academic_year_start = year - 1
    else:  # 7-8月 = 小学期
        xqm = "16"; academic_year_start = year - 1

    xnm = str(academic_year_start)
    term_name = xqm_to_term_name(xnm, xqm)

    # 教学周推算
    week = _estimate_week(today, xqm, academic_year_start)
    week += week_offset

    return {"xnm": xnm, "xqm": xqm, "term_name": term_name, "week": week}


def _estimate_week(today, xqm, academic_year_start):
    """估算教学周数 (近似)"""
    if xqm == "3":       # 第一学期: 9月1日开学
        start = datetime.date(academic_year_start, 9, 1)
    elif xqm == "12":    # 第二学期: 3月1日开学
        start = datetime.date(academic_year_start + 1, 3, 1)
    else:                # 小学期: 7月1日
        start = datetime.date(academic_year_start + 1, 7, 1)

    delta = (today - start).days
    week = max(1, min(20, delta // 7 + 1))
    return week


# ── 学期工具函数 ────────────────────────────────────────────

def xqm_to_term_name(xnm: str, xqm: str) -> str:
    """将教务xnm/xqm码转为可读学期名。
    xqm: 3→第一学期(秋季), 12→第二学期(春季), 16→第三学期/小学期
    例: ('2025', '3') → '2025-2026-1'"""
    suffix = {'3': '1', '12': '2', '16': '3'}.get(xqm, '?')
    return f"{xnm}-{int(xnm)+1}-{suffix}"


def generate_semester_list(years_back: int = 2) -> list:
    """动态生成要查询的(xnm, xqm)列表，覆盖最近N个学年。"""
    today = datetime.date.today()
    current_year = today.year
    semesters = []
    for year in range(current_year - years_back, current_year + 1):
        for xqm in ['3', '12', '16']:
            semesters.append((str(year), xqm))
    return semesters


def get_time_context(week_offset: int = 0, semester_override: str = "") -> str:
    """生成注入Agent的时间上下文"""
    if semester_override:
        return f"当前学期: {semester_override} (用户手动设置)"
    sem = get_current_semester(week_offset)
    return f"当前学期: {sem['term_name']} (xnm={sem['xnm']}, xqm={sem['xqm']}), 第{sem['week']}教学周"


# ── CLI ─────────────────────────────────────────────────────
if __name__ == "__main__":
    sem = get_current_semester()
    print(f"推算结果: {sem}")
    print(f"上下文: {get_time_context()}")
