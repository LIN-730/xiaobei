# crawlers/selected_courses.py — 选课结果查询 (GNMKDM: N253512)
# 使用 BrowserCrawler (Playwright) 拦截Grid数据API
# 按时段开关: is_selection_period() 在非选课期自动跳过
import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from crawlers.base import BaseCrawler
from database import replace_table_data
from user_profile import get_current_semester


def is_selection_period() -> bool:
    """
    判断当前是否处于选课期间。

    基于学期推算:
    - 秋季学期选课: 8月下旬 ~ 9月中旬
    - 春季学期选课: 2月中旬 ~ 3月中旬
    - 小学期选课: 6月下旬 ~ 7月上旬

    也检查数据库中历史选课通知来校准（未来扩展）。

    Returns:
        True: 当前可能处于选课期
    """
    now = datetime.now()
    month, day = now.month, now.day

    # 秋季选课窗口: 8月20日 ~ 9月20日
    if month == 8 and day >= 20:
        return True
    if month == 9 and day <= 20:
        return True

    # 春季选课窗口: 2月15日 ~ 3月15日
    if month == 2 and day >= 15:
        return True
    if month == 3 and day <= 15:
        return True

    # 小学期选课窗口: 6月20日 ~ 7月5日
    if month == 6 and day >= 20:
        return True
    if month == 7 and day <= 5:
        return True

    return False


def get_next_selection_window() -> Optional[str]:
    """
    返回下一个选课窗口的描述。
    用于告知用户当前不在选课期，以及下次选课的大致时间。
    """
    now = datetime.now()
    month, day = now.month, now.day

    if month < 2 or (month == 2 and day < 15):
        return "春季选课 (预计2月中旬)"
    elif month < 6 or (month == 6 and day < 20):
        return "小学期选课 (预计6月下旬)"
    elif month < 8 or (month == 8 and day < 20):
        return "秋季选课 (预计8月下旬)"
    else:
        return "春季选课 (预计2月中旬)"


class SelectedCourseCrawler(BaseCrawler):
    """
    爬取选课结果。仅在选课期间运行。

    工作流程:
    1. is_selection_period() 判断是否选课期 → 非选课期跳过
    2. BrowserCrawler 导航到选课结果页面 (GNMKDM=N253512)
    3. Grid组件自动加载 → 拦截AJAX数据响应
    4. 解析响应 → 映射到 SelectedCourse 表

    页面: /jwglxt/xsxk/xsxk_cxXsxkResult.html
    """

    GNMKDM = "N253512"
    TABLE_NAME = "SelectedCourse"

    PAGE_PATH = "/jwglxt/xsxk/xsxk_cxXsxkResult.html"
    DATA_PATTERN = "xsxk"  # 选课数据API的URL匹配模式

    def crawl(self, force: bool = False, **kwargs) -> Optional[List[Dict[str, Any]]]:
        """
        爬取选课结果。

        Args:
            force: 强制爬取（忽略选课期检查）
        """
        self._log_start("选课结果")

        # ── 选课期检查 ──
        if not force and not is_selection_period():
            next_window = get_next_selection_window()
            self._log_skip("选课结果",
                          f"非选课期（下次窗口: {next_window}）。使用 force=True 强制爬取。")
            return None

        from crawlers.browser_base import BrowserCrawler

        browser = BrowserCrawler(self.session, headless=True)

        # ── BrowserCrawler 模式 ──
        page_url = f"{self.PAGE_PATH}?gnmkdm={self.GNMKDM}"
        try:
            raw_data = asyncio.run(
                browser.navigate_and_capture(
                    page_url=page_url,
                    data_pattern=self.DATA_PATTERN,
                    wait_ms=4000,
                )
            )
            if raw_data:
                result = self._parse_selected_course_data(raw_data)
                if result:
                    self._log_done("选课结果", len(result))
                    return result
        except Exception as e:
            print(f"   ⚠️  BrowserCrawler失败: {e}")

        # ── 直接POST探针 ──
        print("   🔍 尝试直接POST探针...")
        result = self._probe_direct()
        if result:
            self._log_done("选课结果", len(result))
            return result

        self._log_skip("选课结果", "未获取到有效数据（可能选课期已结束或无选课数据）")
        return None

    def _probe_direct(self) -> Optional[List[Dict[str, Any]]]:
        """
        直接POST探针模式。
        选课结果页面可能允许不带参数的默认查询。
        """
        # 尝试多种可能的POST参数组合
        post_data_variants = [
            # 变体1: 不带参数（默认返回当前学期选课结果）
            {"xnm": "", "xqm": "", "kch": "", "kc": ""},
            # 变体2: 带当前学期
            {"xnm": "", "xqm": "", "xh_id": self.student_no},
        ]

        for post_data in post_data_variants:
            result = self._probe_api(
                path=self.PAGE_PATH,
                data=post_data,
                gnmkdm=self.GNMKDM,
                module_name="选课结果-Direct",
            )
            if result:
                parsed = self._parse_selected_course_data(result)
                if parsed:
                    return parsed

        return None

    def _parse_selected_course_data(self, data: Any) -> Optional[List[Dict[str, Any]]]:
        """
        解析选课结果数据，映射到 SelectedCourse 表。

        支持的响应格式:
        - {"items": [{...}, ...]}  (Grid标准格式)
        - {"rows": [{...}, ...]}
        - [{"kcmc": "课名", ...}, ...]  (直接列表)
        """
        items = None

        if isinstance(data, dict):
            for key in ("items", "rows", "list", "xkList"):
                if key in data and isinstance(data[key], list):
                    items = data[key]
                    break

        elif isinstance(data, list):
            items = data

        if not items:
            print(f"   ⚠️  选课数据无有效列表字段")
            return None

        result = []
        for item in items:
            if not isinstance(item, dict):
                continue

            # 字段映射 (正方教务选课结果 → SelectedCourse表)
            result.append({
                "StudentNo": (
                    item.get("xh_id") or item.get("xh") or
                    item.get("studentNo") or self.student_no
                ),
                "CourseCode": (
                    item.get("kch") or item.get("kcdm") or
                    item.get("courseCode", "")
                ),
                "CourseName": (
                    item.get("kcmc") or item.get("kcm") or
                    item.get("courseName", "")
                ),
                "Teacher": (
                    item.get("xm") or item.get("jsxm") or
                    item.get("teacher") or item.get("jsm", "")
                ),
                "Credit": float(
                    item.get("xf") or item.get("credit") or
                    item.get("xfz") or 0
                ),
                "CourseType": (
                    item.get("kclxmc") or item.get("kclx") or
                    item.get("courseType") or item.get("kclbmc", "")
                ),
                "Classroom": (
                    item.get("cdmc") or item.get("classroom") or
                    item.get("jsmc") or item.get("jasmc", "")
                ),
                "WeekDay": int(
                    item.get("xingqi") or item.get("weekDay") or
                    item.get("xq", 0)
                ),
                "StartNode": int(
                    item.get("ksjc") or item.get("startNode") or
                    item.get("djj", 0)
                ),
                "EndNode": int(
                    item.get("jsjc") or item.get("endNode") or 0
                ),
                "WeekRange": (
                    item.get("zcmc") or item.get("weekRange") or
                    item.get("zczh", "")
                ),
                "SelectType": (
                    item.get("xklxmc") or item.get("xklx") or
                    item.get("selectType") or item.get("xklbmc", "")
                ),
            })

        return result

    def save_to_db(self, data: List[Dict]) -> int:
        return replace_table_data(self.TABLE_NAME, self.student_no, data)
