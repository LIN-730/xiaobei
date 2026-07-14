# crawlers/training_plan.py — 教学执行计划/培养方案 (GNMKDM: N153540)
# ✅ 已确认: API = pageURL + ?doType=query, POST xh参数
#
# 两层数据:
#   1. 概要列表 (crawl): 专业/年级/总学分 — 返回 jxzxjhxx_id
#   2. 课程详情 (crawl_plan_detail): 通过 jxzxjhxx_id 二次查询，返回完整课程树
#      - 每个模块组下的每门课程: 课程代码/名称/学分/类型/学期/是否必修
#      - 这是学业规划引擎 (Phase 3) 的核心数据源
from typing import List, Dict, Any, Optional
from crawlers.base import BaseCrawler
from database import get_db_conn


class TrainingPlanCrawler(BaseCrawler):
    """
    爬取培养方案。

    两层查询:
    1. crawl() → 概要列表（专业/年级/总学分/jxzxjhxx_id）
    2. crawl_plan_detail(jxzxjhxx_id) → 完整课程树（每门课的代码/名称/学分/类型/学期）
    """

    API_PATH = "/jwglxt/jxzxjhgl/jxzxjhck_cxJxzxjhckIndex.html"
    GNMKDM = "N153540"
    TABLE_NAME = "TrainingPlan"

    # ── 第一层: 概要列表 ────────────────────────────────────────────

    def crawl(self) -> Optional[List[Dict[str, Any]]]:
        """
        爬取培养方案概要列表。
        返回: [{"Major": ..., "Grade": ..., "PlanId": ..., ...}, ...]
        """
        self._log_start("培养方案")

        resp = self._post_api(
            self.API_PATH,
            data={"xh": self.student_no},
            gnmkdm=self.GNMKDM,
            extra_params="doType=query",
        )
        data = self._safe_json(resp, "培养方案")
        if not data:
            return []

        items = data.get("items") or []
        if not items:
            self._log_done("培养方案", 0)
            return []

        result = []
        for item in items:
            if not isinstance(item, dict):
                continue
            result.append({
                "Major": item.get("zymc", ""),
                "Grade": item.get("njmc", ""),
                "CourseCode": item.get("jxzxjhxx_id", ""),  # 方案ID (用于二次查询)
                "CourseName": item.get("dlbs", ""),         # 大类标识(专业/班级)
                "Credit": float(item.get("zdxf", 0) or 0),  # 总学分
                "CourseType": item.get("rwbj", ""),          # 任务标记
                "ModuleGroup": item.get("xqmc", ""),         # 校区
                "Semester": item.get("xz", ""),              # 学制
                "IsRequired": 1 if item.get("sfgazy") == "否" else 0,
            })

        self._log_done("培养方案", len(result))
        return result

    # ── 第二层: 课程详情 (Phase 3.0 核心) ───────────────────────────

    def crawl_plan_detail(self, jxzxjhxx_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        通过方案ID二次查询，获取该培养方案下的完整课程树。

        这是学业规划引擎的核心数据源，返回每门课程的：
        - 课程代码/名称/学分/类型/模块组/建议学期/是否必修

        Args:
            jxzxjhxx_id: 培养方案ID（从 crawl() 的 CourseCode 字段获取）

        Returns:
            课程列表，每门课一条记录
        """
        print(f"   🔍 查询培养方案详情: {jxzxjhxx_id}")

        # 二次查询: 同一API路径，POST数据带上 jxzxjhxx_id
        resp = self._post_api(
            self.API_PATH,
            data={
                "xh": self.student_no,
                "jxzxjhxx_id": jxzxjhxx_id,
            },
            gnmkdm=self.GNMKDM,
            extra_params="doType=query",
        )
        data = self._safe_json(resp, f"培养方案详情({jxzxjhxx_id[:8]}...)")
        if not data:
            print(f"   ⚠️  详情查询返回空: {jxzxjhxx_id}")
            return None

        # 响应结构可能是:
        # {"items": [{课程1}, {课程2}, ...]}  — 扁平课程列表
        # {"items": [{模块组, children: [{课程}, ...]}, ...]}  — 树形结构
        items = data.get("items") or []

        if not items:
            print(f"   ⚠️  详情无课程数据: {jxzxjhxx_id}")
            return None

        # 检测响应结构
        courses = self._extract_courses_from_items(items, jxzxjhxx_id)

        print(f"   ✅ 方案 {jxzxjhxx_id[:8]}... 包含 {len(courses)} 门课程")
        return courses

    def _extract_courses_from_items(
        self, items: List[Dict], plan_id: str
    ) -> List[Dict[str, Any]]:
        """
        从培养方案详情响应中提取课程列表。
        支持扁平结构和树形结构两种响应格式。
        """
        courses = []

        for item in items:
            if not isinstance(item, dict):
                continue

            # 检查是否有 children/subCourses 子节点 (树形结构: 模块组 → 课程)
            children = (
                item.get("children") or
                item.get("subCourses") or
                item.get("kckList") or
                []
            )

            if children:
                # 树形结构: item 是模块组, children 是课程列表
                module_name = (
                    item.get("mkName") or item.get("mkmc") or
                    item.get("moduleName") or item.get("mkdm") or ""
                )
                for child in children:
                    if not isinstance(child, dict):
                        continue
                    # 递归处理嵌套模块组
                    grand_children = (
                        child.get("children") or
                        child.get("subCourses") or
                        child.get("kckList") or
                        []
                    )
                    if grand_children:
                        courses.extend(
                            self._extract_courses_from_items([child], plan_id)
                        )
                    else:
                        course = self._map_course(child, module_name)
                        if course:
                            courses.append(course)
            else:
                # 扁平结构: item 直接是课程
                course = self._map_course(item, "")
                if course:
                    courses.append(course)

        return courses

    def _map_course(self, item: Dict, default_module: str = "") -> Optional[Dict[str, Any]]:
        """
        将单条课程数据映射为 TrainingPlan 表字段。

        支持的字段名变体（正方教务不同版本可能用不同字段名）：
        """
        course_name = (
            item.get("kcmc") or item.get("kcm") or
            item.get("courseName") or ""
        )
        if not course_name:
            return None  # 跳过无名称的记录

        return {
            "Major": item.get("zymc", ""),
            "Grade": item.get("njmc", ""),
            "CourseCode": (
                item.get("kch") or item.get("kcdm") or
                item.get("courseCode", "")
            ),
            "CourseName": course_name,
            "Credit": float(
                item.get("xf") or item.get("credit") or
                item.get("xfz") or 0
            ),
            "CourseType": (
                item.get("kclxmc") or item.get("kclx") or
                item.get("courseType") or item.get("kclbmc", "")
            ),
            "ModuleGroup": (
                item.get("mkName") or item.get("mkmc") or
                item.get("moduleName") or default_module or
                item.get("mkdm", "")
            ),
            "Semester": (
                item.get("kkxq") or item.get("semester") or
                item.get("kkxqmc") or item.get("term", "")
            ),
            "IsRequired": (
                1 if item.get("kclxmc") in ("必修", "公共必修", "专业必修") else
                1 if item.get("sfbx") in ("1", "是", 1) else
                1 if item.get("isRequired") in (True, "1", 1) else 0
            ),
        }

    # ── 批量获取所有方案的详细课程 ──────────────────────────────────

    def crawl_all_courses(self) -> Optional[List[Dict[str, Any]]]:
        """
        获取所有培养方案的完整课程列表。
        先调用 crawl() 获取方案列表，再逐个查询详情。

        Returns:
            所有方案下的所有课程（去重），用于学业规划引擎。
        """
        self._log_start("培养方案-全部课程")

        # 第一步: 获取方案概要
        plans = self.crawl()
        if not plans:
            self._log_skip("培养方案-全部课程", "无方案概要数据")
            return None

        # 第二步: 逐个查询详情
        all_courses = {}
        for plan in plans:
            plan_id = plan.get("CourseCode", "")
            if not plan_id:
                continue

            major = plan.get("Major", "")
            grade = plan.get("Grade", "")

            try:
                courses = self.crawl_plan_detail(plan_id)
                if courses:
                    # 补充 Major/Grade 信息（详情响应可能不包含）
                    for c in courses:
                        if not c.get("Major"):
                            c["Major"] = major
                        if not c.get("Grade"):
                            c["Grade"] = grade
                        # 用 (课程代码+名称) 去重
                        key = f"{c['CourseCode']}-{c['CourseName']}"
                        if key not in all_courses:
                            all_courses[key] = c
            except Exception as e:
                print(f"   ⚠️  方案 {plan_id[:8]}... 详情查询失败: {e}")
                continue

        result = list(all_courses.values())
        self._log_done("培养方案-全部课程", len(result))
        return result

    # ── 数据库保存 ──────────────────────────────────────────────────

    def save_to_db(self, data: List[Dict]) -> int:
        if not data:
            return 0
        conn = get_db_conn()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM TrainingPlan")
            cols = list(data[0].keys())
            ph = ", ".join(["?"] * len(cols))
            sql = f"INSERT INTO TrainingPlan ({', '.join(cols)}) VALUES ({ph})"
            for r in data:
                cur.execute(sql, [r.get(c, "") for c in cols])
            conn.commit()
            return len(data)
        except Exception as e:
            conn.rollback()
            print(f"  [培养方案] 保存失败: {e}")
            return 0
        finally:
            cur.close()
            conn.close()


if __name__ == "__main__":
    from crawlers.auth import login_edu
    sess = login_edu()
    if sess:
        crawler = TrainingPlanCrawler(sess)

        # 测试第一层: 概要
        data = crawler.crawl()
        if data:
            print(f"\n培养方案概要: {len(data)} 个")
            for d in data[:3]:
                print(f"  {d['Major']} {d['Grade']} — 总学分: {d['Credit']} (ID: {d['CourseCode'][:20]}...)")

            # 测试第二层: 第一个方案的详细课程
            plan_id = data[0].get("CourseCode", "")
            if plan_id:
                print(f"\n--- 查询方案详情: {plan_id} ---")
                courses = crawler.crawl_plan_detail(plan_id)
                if courses:
                    print(f"课程详情: {len(courses)} 门")
                    for c in courses[:10]:
                        print(f"  [{c['CourseType'] or '?'}] {c['CourseName']} "
                              f"{c['Credit']}学分 模块:{c['ModuleGroup'] or '?'} "
                              f"学期:{c['Semester'] or '?'} "
                              f"{'必修' if c['IsRequired'] else '选修'}")
