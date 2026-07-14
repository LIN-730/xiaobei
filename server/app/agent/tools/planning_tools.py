# tools/planning_tools.py — 学业规划 Agent 工具 (异步版, P3)
"""
4个 Agent 工具，封装 PlanningEngine 的核心功能:
  - analyze_credit_gap: 学分缺口分析
  - check_required_courses: 必修课提醒
  - recommend_courses: 选课推荐
  - plan_academic_path: 学业路径规划
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.agent.planning_engine import PlanningEngine


def _format_module_list(modules: list, max_items: int = 15) -> str:
    """格式化模块组列表为可读文本"""
    lines = []
    for m in modules[:max_items]:
        name = m.get("name", "?")
        required = m.get("required", 0)
        earned = m.get("earned", 0)
        remaining = m.get("remaining", 0)
        status = m.get("status", "?")
        status_icon = {"completed": "✅", "in_progress": "🔄", "not_started": "⬜"}.get(status, "❓")
        pct = f"{earned}/{required}" if required > 0 else f"{earned}/?"
        lines.append(f"  {status_icon} {name}: {pct}学分 (缺{remaining}学分)")
    if len(modules) > max_items:
        lines.append(f"  ... 还有{len(modules) - max_items}个模块组")
    return "\n".join(lines)


async def analyze_credit_gap(db: AsyncSession, user_id: str, student_no: str) -> str:
    """
    分析学分缺口：按模块组对比已修学分 vs 要求学分。
    触发词：「学分缺口」「还差多少学分」「毕业还差什么」「模块进度」「学分分析」。
    """
    try:
        engine = PlanningEngine(db, user_id, student_no)
        result = await engine.analyze_credit_gap()

        if "error" in result:
            return f"⚠️ {result['error']}"

        lines = [
            f"📊 学分缺口分析",
            f"总要求: {result['total_required']}学分 | 已获: {result['total_earned']}学分 | 剩余: {result['total_remaining']}学分 | GPA: {result['gpa']}",
            "",
            f"模块组详情 ({len(result['modules'])}个):",
            _format_module_list(result['modules']),
        ]

        critical_missing = []
        for m in result["modules"]:
            for mc in m.get("missing_courses", []):
                if mc.get("required"):
                    critical_missing.append(
                        f"  ❌ [{m['name']}] {mc['name']} {mc['credit']}学分 (必修未修)"
                    )

        if critical_missing:
            lines.append("\n🔴 关键缺失 (必修课):")
            lines.extend(critical_missing[:10])
            if len(critical_missing) > 10:
                lines.append(f"  ... 还有{len(critical_missing) - 10}门")

        return "\n".join(lines)

    except Exception as e:
        return f"学分缺口分析失败: {e}"


async def check_required_courses(db: AsyncSession, user_id: str, student_no: str) -> str:
    """
    检查必修课完成情况：哪些必修课还没修或没通过。
    触发词：「必修课」「还有哪些必修」「必修修完了吗」「必修进度」。
    """
    try:
        engine = PlanningEngine(db, user_id, student_no)
        result = await engine.check_required_courses()

        if "error" in result:
            return f"⚠️ {result['error']}"

        lines = [
            f"📋 必修课检查",
            f"共{result['total_required_courses']}门必修 | "
            f"✅已通过{result['completed']}门 | "
            f"🔄进行中{result['in_progress']}门 | "
            f"❌未修{result['missing']}门",
        ]

        if result["in_progress"] > 0:
            lines.append("\n🔄 进行中:")
            for c in result.get("in_progress_list", [])[:10]:
                lines.append(f"  {c['name']} {c['credit']}学分 [{c['module']}]")

        if result["missing"] > 0:
            lines.append("\n❌ 未修必修课:")
            for c in result.get("missing_list", [])[:15]:
                lines.append(
                    f"  {c['name']} {c['credit']}学分 [{c['module']}] (建议学期: {c['semester'] or '?'})"
                )
            if result["missing"] > 15:
                lines.append(f"  ... 还有{result['missing'] - 15}门")

        if result["missing"] == 0 and result["in_progress"] == 0:
            lines.append("\n🎉 全部必修课已完成！")

        return "\n".join(lines)

    except Exception as e:
        return f"必修课检查失败: {e}"


async def recommend_courses(
    db: AsyncSession,
    user_id: str,
    student_no: str,
    target_semester: Optional[str] = None,
    max_count: Optional[int] = None,
) -> str:
    """
    基于学分缺口推荐下学期选课。
    参数: target_semester(可选, 如"2025-2026-1")，max_count(可选, 最多推荐数, 默认10)。
    触发词：「选课推荐」「下学期选什么」「推荐选课」「选课建议」。
    """
    try:
        engine = PlanningEngine(db, user_id, student_no)
        kwargs = {}
        if target_semester:
            kwargs["target_semester"] = target_semester
        if max_count:
            kwargs["max_recommendations"] = max_count

        result = await engine.recommend_courses(**kwargs)

        if "error" in result:
            return f"⚠️ {result['error']}"

        lines = [
            f"📚 选课推荐 — {result['target_semester']}",
            f"共推荐{len(result['recommendations'])}门课, 合计{result['total_credit']}学分",
            "",
        ]

        priority_order = ["required_missing", "required_module", "elective"]
        priority_labels = {
            "required_missing": "🔴 必修未修 (最优先)",
            "required_module": "🟡 模块必修",
            "elective": "🟢 模块选修",
        }

        for priority in priority_order:
            group = [r for r in result["recommendations"] if r["priority"] == priority]
            if not group:
                continue
            lines.append(f"{priority_labels[priority]} ({len(group)}门):")
            for r in group:
                lines.append(f"  {r['name']} {r['credit']}学分 [{r['module']}] {r['semester'] or ''}")
            lines.append("")

        return "\n".join(lines)

    except Exception as e:
        return f"选课推荐失败: {e}"


async def plan_academic_path(
    db: AsyncSession,
    user_id: str,
    student_no: str,
    credits_per_semester: Optional[float] = None,
) -> str:
    """
    规划剩余学期的学业路径：每学期应修哪些必修课。
    参数: credits_per_semester(可选, 每学期目标学分，默认25)。
    触发词：「学业规划」「怎么安排选课」「毕业规划」「学期计划」「还剩几学期」。
    """
    try:
        engine = PlanningEngine(db, user_id, student_no)
        kwargs = {}
        if credits_per_semester:
            kwargs["target_credits_per_semester"] = credits_per_semester

        result = await engine.plan_path(**kwargs)

        if "error" in result:
            return f"⚠️ {result['error']}"

        lines = [
            f"🗓️ 学业路径规划",
            f"剩余{result['remaining_semesters']}学期 | 待修{result['total_remaining_credits']}学分",
            "",
        ]

        for sp in result["semester_plans"]:
            sem = sp["semester"]
            count = sp["course_count"]
            credit = sp["total_credit"]
            lines.append(f"📅 {sem} ({count}门, {credit}学分):")
            for c in sp["courses"][:8]:
                lines.append(f"  {c['name']} {c['credit']}学分 [{c['module']}]")
            if count > 8:
                lines.append(f"  ... 还有{count - 8}门")
            lines.append("")

        if result.get("unassigned_courses"):
            lines.append(f"⚠️ 超出规划容量未分配的课程 ({len(result['unassigned_courses'])}门):")
            for c in result["unassigned_courses"][:5]:
                lines.append(f"  {c['name']} {c['credit']}学分")

        return "\n".join(lines)

    except Exception as e:
        return f"学业路径规划失败: {e}"
