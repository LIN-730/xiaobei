# planning_engine.py — 学业规划引擎 (异步版, P3)
"""
数据源:
  - AcademicStatus: 模块组学分进度 (RawData JSON: required/earned/remaining)
  - TrainingPlan: 培养方案课程树 (Code/Name/Credit/Type/ModuleGroup/Semester/IsRequired)
  - Score: 历史成绩 (Code/Name/Score/Credit/GradePoint/Term)
  - SelectedCourse: 当前已选课程
  - Student: 年级/专业/学制

学期计算:
  - xqm=3(秋9-1月) xqm=12(春3-6月) xqm=16(小学期7-8月)
  - term_name: {xnm}-{int(xnm)+1}-{1/2/3}

异步改造:
  - SQLite → Repository (async)
  - def → async def
  - student_no 单用户 → user_id 多用户隔离
"""
from __future__ import annotations

import ast
from typing import Dict, List, Optional, Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.repos import (
    AcademicStatusRepo,
    TrainingPlanRepo,
    ScoreRepo,
    SelectedCourseRepo,
    StudentRepo,
)
from app.agent.user_profile import get_current_semester, xqm_to_term_name


class PlanningEngine:
    """学业规划引擎 — 学分缺口 → 必修提醒 → 选课推荐 → 学业路径"""

    def __init__(self, db: AsyncSession, user_id: str, student_no: str):
        self.db = db
        self.user_id = user_id
        self.student_no = student_no
        # 懒初始化 repos
        self._academic_status_repo = AcademicStatusRepo(db, user_id)
        self._training_plan_repo = TrainingPlanRepo(db, user_id)
        self._score_repo = ScoreRepo(db, user_id)
        self._selected_course_repo = SelectedCourseRepo(db, user_id)
        self._student_repo = StudentRepo(db, user_id)

    # ═══════════════════════════════════════════════════════════════
    # 3.1 学分缺口分析
    # ═══════════════════════════════════════════════════════════════

    async def analyze_credit_gap(self) -> Dict[str, Any]:
        """
        分析学分缺口: 按模块组对比 required vs earned。

        Returns:
            {
                "total_required": float, "total_earned": float, "total_remaining": float,
                "gpa": float,
                "modules": [{name, required, earned, remaining, status, missing_courses, ...}],
                "summary": str
            }
        """
        # 1. 获取学业进度
        status = await self._academic_status_repo.get_status()
        if not status:
            return {"error": "未找到学业情况数据，请先同步教务数据。"}

        total_required = float(status.total_credits or 0)
        total_earned = float(status.earned_credits or 0)
        failed_credits = float(status.failed_credits or 0)
        total_remaining = total_required - total_earned
        gpa = float(status.average_gpa or 0)
        raw_data = status.raw_data or "[]"

        # 2. 解析模块组详情
        try:
            modules_raw = ast.literal_eval(raw_data) if isinstance(raw_data, str) else raw_data
        except (ValueError, SyntaxError):
            modules_raw = []

        # 3. 获取所有培养方案课程
        plan_courses = await self._training_plan_repo.get_all()

        # 4. 获取所有成绩
        scores = await self._score_repo.get_all()

        # 5. 获取已选课程
        selected = await self._selected_course_repo.get_all()

        # 6. 构建已通过课程集合
        passed_codes: set = set()
        for s in scores:
            code = s.course_code or s.course_name
            if self._is_passed(str(s.score or "").strip()):
                passed_codes.add(code)

        selected_codes: set = set()
        for sc in selected:
            selected_codes.add(sc.course_code or sc.course_name)

        # 7. 按模块组分组培养方案课程
        plan_by_module: Dict[str, List[Dict]] = {}
        for c in plan_courses:
            module = c.module_group or "未分类"
            plan_by_module.setdefault(module, []).append({
                "code": c.course_code or "",
                "name": c.course_name or "",
                "credit": float(c.credit or 0),
                "type": c.course_type or "",
                "semester": c.semester or "",
                "required": bool(c.is_required),
            })

        # 8. 构建模块缺口
        module_credits_from_status: Dict[str, Dict] = {}
        for m in modules_raw:
            if isinstance(m, dict):
                name = m.get("name", "")
                module_credits_from_status[name] = {
                    "required": float(m.get("required", 0)),
                    "earned": float(m.get("earned", 0)),
                    "remaining": float(m.get("remaining", 0)),
                }

        all_module_names = set(module_credits_from_status.keys()) | set(plan_by_module.keys())

        modules_result = []
        for module_name in sorted(all_module_names):
            status_info = module_credits_from_status.get(module_name, {})
            plan_courses_in_module = plan_by_module.get(module_name, [])

            required = status_info.get("required", 0)
            earned = status_info.get("earned", 0)
            remaining = status_info.get("remaining", 0)

            if not status_info and plan_courses_in_module:
                required = sum(c["credit"] for c in plan_courses_in_module if c["required"])
                required = round(required, 1)

            missing_courses = []
            for c in plan_courses_in_module:
                ckey = c["code"] or c["name"]
                if ckey and ckey not in passed_codes and ckey not in selected_codes:
                    missing_courses.append({
                        "code": c["code"],
                        "name": c["name"],
                        "credit": c["credit"],
                        "required": c["required"],
                        "semester": c["semester"],
                    })

            if remaining <= 0 and earned > 0:
                mod_status = "completed"
            elif earned > 0:
                mod_status = "in_progress"
            else:
                mod_status = "not_started"

            modules_result.append({
                "name": module_name,
                "required": required,
                "earned": earned,
                "remaining": remaining if remaining > 0 else max(0, required - earned),
                "status": mod_status,
                "missing_courses": missing_courses,
                "total_courses_in_plan": len(plan_courses_in_module),
            })

        # 9. 摘要
        completed_modules = sum(1 for m in modules_result if m["status"] == "completed")
        in_progress_mods = sum(1 for m in modules_result if m["status"] == "in_progress")
        not_started_mods = sum(1 for m in modules_result if m["status"] == "not_started")

        summary = (
            f"学分缺口分析: 总要求{total_required}学分, 已获{total_earned}学分, "
            f"未通过{failed_credits}学分, GPA {gpa}\n"
            f"模块组: {len(modules_result)}个 "
            f"({completed_modules}已完成, {in_progress_mods}进行中, {not_started_mods}未开始)"
        )

        return {
            "total_required": total_required,
            "total_earned": total_earned,
            "total_remaining": total_remaining,
            "failed_credits": failed_credits,
            "gpa": gpa,
            "modules": modules_result,
            "summary": summary,
        }

    # ═══════════════════════════════════════════════════════════════
    # 3.2 必修课提醒
    # ═══════════════════════════════════════════════════════════════

    async def check_required_courses(self) -> Dict[str, Any]:
        """
        检查必修课完成情况: 标记必修但未修/未通过的课程。
        """
        # 1. 必修课列表
        required_courses = await self._training_plan_repo.get_all(is_required=1)
        if not required_courses:
            return {"error": "培养方案中未找到必修课数据，请先同步培养方案。"}

        # 2. 已通过课程
        scores = await self._score_repo.get_all()
        passed_codes: set = set()
        for s in scores:
            code = s.course_code or s.course_name
            if self._is_passed(str(s.score or "").strip()):
                passed_codes.add(code)

        # 3. 已选课程
        selected = await self._selected_course_repo.get_all()
        selected_codes: set = set()
        for sc in selected:
            selected_codes.add(sc.course_code or sc.course_name)

        # 4. 分类
        completed = []
        in_progress = []
        missing = []

        for c in required_courses:
            ckey = c.course_code or c.course_name
            course_info = {
                "code": c.course_code or "",
                "name": c.course_name or "",
                "credit": float(c.credit or 0),
                "module": c.module_group or "",
                "semester": c.semester or "",
            }
            if ckey in passed_codes:
                completed.append(course_info)
            elif ckey in selected_codes:
                in_progress.append(course_info)
            else:
                missing.append(course_info)

        summary = (
            f"必修课: 共{len(required_courses)}门, "
            f"已通过{len(completed)}门, "
            f"进行中{len(in_progress)}门, "
            f"未修{len(missing)}门"
        )

        return {
            "total_required_courses": len(required_courses),
            "completed": len(completed),
            "completed_list": completed,
            "in_progress": len(in_progress),
            "in_progress_list": in_progress,
            "missing": len(missing),
            "missing_list": missing,
            "summary": summary,
        }

    # ═══════════════════════════════════════════════════════════════
    # 3.3 选课推荐
    # ═══════════════════════════════════════════════════════════════

    async def recommend_courses(
        self,
        target_semester: str = None,
        max_recommendations: int = 10,
    ) -> Dict[str, Any]:
        """
        基于学分缺口推荐选课。
        """
        # 确定目标学期
        if not target_semester:
            current = get_current_semester()
            cur_xnm = current["xnm"]
            cur_xqm = current["xqm"]
            if cur_xqm == "3":
                next_xnm, next_xqm = cur_xnm, "12"
            elif cur_xqm == "12":
                next_xnm, next_xqm = cur_xnm, "16"
            else:
                next_xnm, next_xqm = str(int(cur_xnm) + 1), "3"
            target_semester = xqm_to_term_name(next_xnm, next_xqm)

        # 1. 获取缺口
        gap = await self.analyze_credit_gap()
        if "error" in gap:
            return gap

        # 2. 获取必修缺失
        required_check = await self.check_required_courses()
        missing_required = required_check.get("missing_list", [])
        missing_required_codes = set(c["code"] or c["name"] for c in missing_required)

        # 3. 所有培养方案课程
        all_plan_courses = await self._training_plan_repo.get_all()

        # 4. 已通过/已选
        scores = await self._score_repo.get_all()
        passed_codes: set = set()
        for s in scores:
            if self._is_passed(str(s.score or "").strip()):
                passed_codes.add(s.course_code or s.course_name)

        selected = await self._selected_course_repo.get_all()
        selected_codes = set(sc.course_code or sc.course_name for sc in selected)

        excluded = passed_codes | selected_codes

        # 5. 缺口模块
        gap_modules = {m["name"]: m["remaining"] for m in gap["modules"] if m["remaining"] > 0}

        recommendations = []

        # 优先级1: 必修缺失
        for c in missing_required:
            recommendations.append({
                "code": c["code"],
                "name": c["name"],
                "credit": c["credit"],
                "module": c["module"],
                "required": True,
                "semester": c["semester"],
                "priority": "required_missing",
                "reason": f"必修课未修 — {c['module']}模块剩余{gap_modules.get(c['module'], '?')}学分",
            })

        # 优先级2: 缺口模块中的其他课程
        for c in all_plan_courses:
            ckey = c.course_code or c.course_name
            if not ckey or ckey in excluded:
                continue
            if ckey in missing_required_codes:
                continue

            module = c.module_group or "未分类"
            if module in gap_modules and gap_modules[module] > 0:
                recommendations.append({
                    "code": c.course_code or "",
                    "name": c.course_name or "",
                    "credit": float(c.credit or 0),
                    "module": module,
                    "required": bool(c.is_required),
                    "semester": c.semester or "",
                    "priority": "required_module" if c.is_required else "elective",
                    "reason": (
                        f"模块'{module}'剩余{gap_modules[module]}学分"
                        f"{' (必修)' if c.is_required else ' (选修)'}"
                    ),
                })

        # 6. 排序: 必修优先 → 学分高优先
        recommendations.sort(key=lambda r: (
            0 if r["priority"] == "required_missing" else
            1 if r["priority"] == "required_module" else 2,
            -r["credit"],
        ))

        recommendations = recommendations[:max_recommendations]
        total_rec_credit = sum(r["credit"] for r in recommendations)

        summary = (
            f"选课推荐 ({target_semester}): "
            f"共推荐{len(recommendations)}门课, "
            f"合计{total_rec_credit}学分"
        )

        return {
            "target_semester": target_semester,
            "recommendations": recommendations,
            "total_credit": round(total_rec_credit, 1),
            "summary": summary,
        }

    # ═══════════════════════════════════════════════════════════════
    # 3.4 学业路径规划
    # ═══════════════════════════════════════════════════════════════

    async def plan_path(self, target_credits_per_semester: float = 25.0) -> Dict[str, Any]:
        """
        规划剩余学期的学业路径。
        """
        # 1. 学生信息
        student = await self._student_repo.get_one()
        if not student:
            return {"error": "未找到学生信息。"}

        grade = int(student.grade or "0")
        edu_level_str = student.edu_level or "4"
        try:
            edu_level = int(edu_level_str)
        except ValueError:
            edu_level = 4

        current = get_current_semester()
        cur_xnm = int(current["xnm"])
        cur_xqm = current["xqm"]

        # 2. 计算剩余学期数
        completed_years = cur_xnm - grade
        if cur_xqm == "3":
            completed_semesters = completed_years * 2
        elif cur_xqm == "12":
            completed_semesters = completed_years * 2 + 1
        else:
            completed_semesters = completed_years * 2 + 2

        total_semesters = edu_level * 2
        remaining_semesters = max(1, total_semesters - completed_semesters)

        # 3. 未修必修课
        required_courses = await self._training_plan_repo.get_all(is_required=1)

        scores = await self._score_repo.get_all()
        passed_codes: set = set()
        for s in scores:
            if self._is_passed(str(s.score or "").strip()):
                passed_codes.add(s.course_code or s.course_name)

        selected = await self._selected_course_repo.get_all()
        selected_codes = set(sc.course_code or sc.course_name for sc in selected)

        excluded = passed_codes | selected_codes

        # 4. 学分缺口
        academic_status = await self._academic_status_repo.get_status()
        total_req = float(academic_status.total_credits or 0) if academic_status else 0
        earned = float(academic_status.earned_credits or 0) if academic_status else 0
        total_remaining_credits = max(0, total_req - earned)

        # 5. 筛选未修必修课
        pending_required = []
        for c in required_courses:
            ckey = c.course_code or c.course_name
            if ckey not in excluded:
                pending_required.append({
                    "code": c.course_code or "",
                    "name": c.course_name or "",
                    "credit": float(c.credit or 0),
                    "module": c.module_group or "",
                    "semester": c.semester or "",
                    "required": True,
                })

        # 6. 生成剩余学期列表
        semester_plan_names = []
        xnm, xqm = cur_xnm, cur_xqm
        for _ in range(remaining_semesters):
            if xqm == "3":
                xnm_next, xqm_next = xnm, "12"
            elif xqm == "12":
                xnm_next, xqm_next = xnm, "16"
            else:
                xnm_next, xqm_next = str(int(xnm) + 1), "3"
            xnm, xqm = xnm_next, xqm_next
            semester_plan_names.append(xqm_to_term_name(str(xnm), xqm))

        # 7. 分配课程到学期
        semester_plans = []
        remaining_courses = list(pending_required)
        for sem_name in semester_plan_names:
            sem_courses = []
            sem_credit = 0.0
            matched = [c for c in remaining_courses if self._semester_match(c["semester"], sem_name)]
            unmatched = [c for c in remaining_courses if not self._semester_match(c["semester"], sem_name)]

            for c in matched + unmatched:
                if sem_credit + c["credit"] <= target_credits_per_semester:
                    sem_courses.append(c)
                    sem_credit += c["credit"]
                    if c in remaining_courses:
                        remaining_courses.remove(c)

            semester_plans.append({
                "semester": sem_name,
                "courses": sem_courses,
                "total_credit": round(sem_credit, 1),
                "course_count": len(sem_courses),
            })

        unassigned = remaining_courses

        # 8. 摘要
        total_planned_credit = sum(p["total_credit"] for p in semester_plans)
        summary = (
            f"学业路径规划: 剩余{remaining_semesters}学期, "
            f"待修学分{total_remaining_credits}, "
            f"已规划{total_planned_credit}学分({len(pending_required)}门必修课)"
        )
        if unassigned:
            summary += f"\n⚠️ {len(unassigned)}门课超出规划容量未分配"

        return {
            "remaining_semesters": remaining_semesters,
            "total_remaining_credits": total_remaining_credits,
            "semester_plans": semester_plans,
            "unassigned_courses": [
                {"code": c["code"], "name": c["name"], "credit": c["credit"]}
                for c in unassigned
            ],
            "summary": summary,
        }

    # ═══════════════════════════════════════════════════════════════
    # 综合报告
    # ═══════════════════════════════════════════════════════════════

    async def full_report(self) -> Dict[str, Any]:
        """
        生成完整的学业规划报告 (3.1 + 3.2 + 3.3 + 3.4)。
        """
        credit_gap = await self.analyze_credit_gap()
        required_check = await self.check_required_courses()
        recommendations = await self.recommend_courses()
        path_plan = await self.plan_path()

        errors = []
        for name, result in [
            ("学分缺口", credit_gap),
            ("必修提醒", required_check),
            ("选课推荐", recommendations),
            ("学业路径", path_plan),
        ]:
            if "error" in result:
                errors.append(f"{name}: {result['error']}")

        overall = (
            f"学业规划报告:\n"
            f"  {credit_gap.get('summary', 'N/A')}\n"
            f"  {required_check.get('summary', 'N/A')}\n"
            f"  {recommendations.get('summary', 'N/A')}\n"
            f"  {path_plan.get('summary', 'N/A')}"
        )
        if errors:
            overall += f"\n\n⚠️ 数据缺失: {'; '.join(errors)}"

        return {
            "credit_gap": credit_gap,
            "required_check": required_check,
            "recommendations": recommendations,
            "path_plan": path_plan,
            "summary": overall,
        }

    # ═══════════════════════════════════════════════════════════════
    # 工具方法 (与原始版本相同)
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def _is_passed(score_str: str) -> bool:
        """判断成绩是否通过"""
        if not score_str:
            return False
        fail_keywords = ["不及格", "缺考", "作弊", "违纪", "取消"]
        for kw in fail_keywords:
            if kw in score_str:
                return False
        pass_keywords = ["优秀", "良好", "中等", "通过", "及格"]
        for kw in pass_keywords:
            if kw in score_str:
                return True
        try:
            return float(score_str) >= 60
        except ValueError:
            return True

    @staticmethod
    def _semester_match(plan_semester: str, target_term: str) -> bool:
        """
        判断培养方案的建议学期是否匹配目标学期。
        plan_semester: "1","2","3"... (第几学期) 或 "2025-2026-1"...
        target_term: "2025-2026-1"...
        """
        if not plan_semester or plan_semester == "未指定":
            return False
        try:
            sem_num = int(plan_semester)
            parts = target_term.split("-")
            if len(parts) == 3:
                target_num = int(parts[2])
                return sem_num == target_num
        except ValueError:
            pass
        return plan_semester == target_term
