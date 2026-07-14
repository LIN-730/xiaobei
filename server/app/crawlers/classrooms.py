# crawlers/classrooms.py — 查询空闲教室 (GNMKDM: N2155)
# 使用 BrowserCrawler (Playwright) 探测并拦截数据API
#
# 页面特征:
#   - JS动态加载校区/教学楼/星期/节次下拉选项
#   - 页面嵌入变量: xxdm='10010', jsdm='xs', jslxdm='02', jg_id='05'
#   - 数据API: /cdjy/cdjy_cxCdsfjy.html (doType=query) 或 /cdjy/cdjy_cxSfkfyuy.html
import asyncio
import json
from typing import List, Dict, Any, Optional
from crawlers.base import BaseCrawler
from database import replace_table_data


class ClassroomCrawler(BaseCrawler):
    """
    爬取空闲教室数据。

    工作流程:
    1. BrowserCrawler 导航到空闲教室页面 (GNMKDM=N2155)
    2. 页面JS自动初始化Grid → 拦截AJAX数据响应
    3. 自动点击"查询"按钮触发数据加载
    4. 解析响应中的教室列表 → 映射到 Classroom 表
    """

    GNMKDM = "N2155"
    TABLE_NAME = "Classroom"

    # 可能的页面/API路径（按优先级尝试）
    PAGE_PATHS = [
        "/jwglxt/cdjy/cdjy_cxCdsfjy.html",
        "/jwglxt/cdjy/cdjy_cxSfkfyuy.html",
    ]
    DATA_PATTERN = "cdjy"  # 教室数据API的URL匹配模式

    def crawl(self, **kwargs) -> Optional[List[Dict[str, Any]]]:
        """
        爬取空闲教室。使用Playwright浏览器自动化。

        可选参数:
            campus: 校区筛选
            building: 教学楼筛选
            week_day: 星期几 (1-7)
        """
        self._log_start("空闲教室")

        from crawlers.browser_base import BrowserCrawler

        browser = BrowserCrawler(self.session, headless=True)

        # 按优先级尝试各个页面路径
        for page_path in self.PAGE_PATHS:
            page_url = f"{page_path}?gnmkdm={self.GNMKDM}"
            try:
                raw_data = asyncio.run(
                    browser.navigate_and_capture(
                        page_url=page_url,
                        data_pattern=self.DATA_PATTERN,
                        wait_ms=4000,  # Grid组件可能需要更长时间初始化
                    )
                )
                if raw_data:
                    result = self._parse_classroom_data(raw_data)
                    if result:
                        self._log_done("空闲教室", len(result))
                        return result
            except Exception as e:
                print(f"   ⚠️  [{page_path}] 浏览器爬取失败: {e}")
                continue

        # BrowserCrawler 失败 → 尝试直接 POST 探针
        print("   🔍 BrowserCrawler未获取数据，尝试直接POST探针...")
        result = self._probe_direct_api()
        if result:
            self._log_done("空闲教室", len(result))
            return result

        self._log_skip("空闲教室", "所有路径均未获取到有效数据")
        return None

    def _probe_direct_api(self) -> Optional[List[Dict[str, Any]]]:
        """
        直接POST探针模式：尝试直接请求数据API。
        用于BrowserCrawler不可用时的fallback探测。
        """
        # 尝试不带校区/教学楼参数的默认查询
        post_data = {
            "xxdm": "10010",       # 学校代码
            "jsdm": "xs",          # 角色代码 (学生)
            "jslxdm": "02",        # 教室类型代码
            "jg_id": "05",         # 机构ID
            "xqdm": "",            # 校区代码（空=全部）
            "jxlId": "",           # 教学楼ID（空=全部）
            "xingqi": "",          # 星期（空=全部）
            "jcStart": "",         # 起始节次
            "jcEnd": "",           # 结束节次
        }

        for page_path in self.PAGE_PATHS:
            api_path = page_path.replace(".html", ".html")
            result = self._probe_api(
                path=api_path,
                data=post_data,
                gnmkdm=self.GNMKDM,
                module_name="空闲教室-Direct",
            )
            if result:
                parsed = self._parse_classroom_data(result)
                if parsed:
                    return parsed

        return None

    def _parse_classroom_data(self, data: Any) -> Optional[List[Dict[str, Any]]]:
        """
        解析教室数据响应，映射到 Classroom 表结构。

        支持的响应格式:
        - {"items": [{...}, ...]}  (Grid标准格式)
        - {"rows": [{...}, ...]}
        - [{"cdmc": "教室名", ...}, ...]  (直接列表)
        """
        items = None

        if isinstance(data, dict):
            # Grid标准格式
            for key in ("items", "rows", "list", "cdList", "cdxxList"):
                if key in data and isinstance(data[key], list):
                    items = data[key]
                    break
            # 可能是单条嵌套
            if items is None and "cdxx" in data:
                items = [data["cdxx"]]

        elif isinstance(data, list):
            items = data

        if not items:
            print(f"   ⚠️  教室数据无有效列表字段，顶层keys: {list(data.keys()) if isinstance(data, dict) else 'list'}")
            return None

        result = []
        for item in items:
            if not isinstance(item, dict):
                continue

            # 字段映射 (正方教务常见字段 → Classroom表)
            result.append({
                "Campus": (
                    item.get("xqmc") or item.get("cdxqmc") or
                    item.get("campus") or item.get("xiaoqu", "")
                ),
                "Building": (
                    item.get("jxlmc") or item.get("jxl") or
                    item.get("building") or item.get("jxldm", "")
                ),
                "RoomNo": (
                    item.get("cdmc") or item.get("cdbh") or
                    item.get("roomNo") or item.get("room", "")
                ),
                "Capacity": int(
                    item.get("cdrs") or item.get("capacity") or
                    item.get("rnrs") or item.get("zws") or 0
                ),
                "WeekDay": int(
                    item.get("xingqi") or item.get("weekDay") or
                    item.get("week_day") or item.get("xq", 0)
                ),
                "StartNode": int(
                    item.get("ksjc") or item.get("startNode") or
                    item.get("start_node") or item.get("djj", 0)
                ),
                "EndNode": int(
                    item.get("jsjc") or item.get("endNode") or
                    item.get("end_node") or 0
                ),
                "WeekRange": (
                    item.get("zcmc") or item.get("weekRange") or
                    item.get("week_range") or item.get("zczh", "")
                ),
                "Status": (
                    item.get("cdzt") or item.get("status") or
                    item.get("syc") or "空闲"
                ),
            })

        return result

    def save_to_db(self, data: List[Dict]) -> int:
        return replace_table_data(self.TABLE_NAME, self.student_no, data)
