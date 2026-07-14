# crawlers/browser_base.py — Playwright浏览器爬虫基类
"""
用于正方教务Grid组件模块的数据爬取。

工作原理:
1. 从 requests.Session 提取 Cookie → 注入 Playwright 浏览器
2. 导航到目标页面 → 页面JS自动初始化Grid → 触发AJAX数据请求
3. 拦截包含实际数据的AJAX响应 → 解析返回

使用方式:
    session = login_edu()  # requests登录
    crawler = ExamCrawler(session)
    data = asyncio.run(crawler.crawl())
"""
import asyncio
import json
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse, parse_qs


class BrowserCrawler:
    """基于Playwright的浏览器爬虫基类"""

    def __init__(self, session, student_no: str, base_url: str = None, headless: bool = True):
        """
        Args:
            session: requests.Session（已登录，含JSESSIONID等Cookie）
            student_no: 学生学号
            base_url: 教务系统根URL
            headless: 是否无头模式
        """
        self.session = session
        self.base_url = base_url or "https://jwglxt.buct.edu.cn"
        self.headless = headless
        self.student_no = student_no

        # 拦截到的数据响应
        self.captured_responses: List[Dict] = []

    # ── Cookie转换 ────────────────────────────────────────────────
    def _get_cookies_for_playwright(self) -> List[Dict]:
        """将requests.Session的Cookie转换为Playwright格式"""
        cookies = []
        for cookie in self.session.cookies:
            cookies.append({
                "name": cookie.name,
                "value": cookie.value,
                "domain": cookie.domain or urlparse(self.base_url).hostname,
                "path": cookie.path or "/",
                "httpOnly": False,
                "secure": cookie.secure or False,
            })
        return cookies

    # ── 核心方法：导航并拦截数据 ──────────────────────────────────
    async def navigate_and_capture(
        self,
        page_url: str,
        data_pattern: str = None,
        wait_ms: int = 3000,
    ) -> Optional[Dict[str, Any]]:
        """
        导航到目标页面，拦截AJAX数据响应。

        Args:
            page_url: 页面完整URL（如 /jwglxt/kwgl/kscx_cxXsksxxIndex.html?gnmkdm=N358105）
            data_pattern: 数据API URL的匹配模式（用于筛选拦截的请求）
            wait_ms: 页面加载后额外等待时间(ms)

        Returns:
            拦截到的JSON数据，失败返回None
        """
        from playwright.async_api import async_playwright

        self.captured_responses = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                locale="zh-CN",
            )

            # 注入Cookie（复用requests登录态）
            cookies = self._get_cookies_for_playwright()
            await context.add_cookies(cookies)

            page = await context.new_page()

            # ── 设置响应拦截器 ──
            async def on_response(response):
                """拦截所有AJAX响应，筛选出数据API的响应"""
                try:
                    url = response.url
                    ct = response.headers.get("content-type", "")

                    # 只关注JSON响应
                    if "application/json" not in ct:
                        return

                    # 排除静态资源和无关请求
                    skip_patterns = [
                        "login_getPublicKey", "login_slogin",
                        "index_initMenu", "getHeader", "getFooter",
                        ".css", ".js", ".png", ".jpg", ".woff",
                    ]
                    if any(p in url for p in skip_patterns):
                        return

                    # 尝试读取响应体
                    body = await response.text()

                    # 排除空的分页模型响应 (totalResult=0)
                    if '"totalResult":"0"' in body and '"totalResult":0' not in body:
                        if len(body) < 500:
                            return  # 空grid，跳过

                    try:
                        data = json.loads(body)
                        self.captured_responses.append({
                            "url": url,
                            "status": response.status,
                            "data": data,
                        })
                    except json.JSONDecodeError:
                        pass

                except Exception:
                    pass  # 拦截器静默处理

            page.on("response", on_response)

            # ── 导航到目标页面 ──
            full_url = f"{self.base_url}{page_url}" if not page_url.startswith("http") else page_url
            print(f"   🌐 导航: {page_url}")
            await page.goto(full_url, wait_until="networkidle", timeout=30000)
            # 等待Grid组件加载并触发AJAX
            await asyncio.sleep(wait_ms / 1000)

            # ── 也可以尝试主动触发查询 ──
            # 有些页面需要点击"查询"按钮才加载数据
            try:
                search_btn = page.locator("button:has-text('查询')")
                if await search_btn.count() > 0:
                    await search_btn.first.click()
                    await asyncio.sleep(1.5)
            except Exception:
                pass

            await browser.close()

        # ── 从拦截结果中找真正的数据 ──
        return self._extract_data_response(data_pattern)

    def _extract_data_response(self, pattern: str = None) -> Optional[Dict]:
        """
        从拦截到的响应中提取真正的数据。
        过滤掉空的分页模型响应，返回包含实际数据的最大响应。
        """
        if not self.captured_responses:
            print("   ⚠️ 未拦截到任何JSON响应")
            return None

        # 优先匹配pattern
        if pattern:
            for r in self.captured_responses:
                if pattern in r["url"]:
                    # 检查是否有实际数据
                    data = r["data"]
                    if isinstance(data, dict):
                        # 排除空grid
                        if data.get("totalResult") == "0" and len(data.keys()) <= 5:
                            continue
                        # 有items/rows/list说明有数据
                        if any(k in data for k in ("items", "rows", "list", "kbList")):
                            print(f"   ✅ 拦截到数据: {r['url'][:80]} ({r['status']})")
                            return data
                    elif isinstance(data, list) and len(data) > 0:
                        print(f"   ✅ 拦截到列表数据: {len(data)}条")
                        return data

        # 否则返回最大的非空响应
        for r in sorted(self.captured_responses,
                        key=lambda x: len(json.dumps(x["data"])),
                        reverse=True):
            data = r["data"]
            if isinstance(data, dict):
                if data.get("totalResult") == "0" and len(data.keys()) <= 5:
                    continue
                if any(k in data for k in ("items", "rows", "list", "kbList")):
                    print(f"   ✅ 拦截到数据: {r['url'][:80]} ({r['status']})")
                    return data
            elif isinstance(data, list) and len(data) > 0:
                return data

        print(f"   ⚠️ 拦截到 {len(self.captured_responses)} 个响应但无有效数据")
        return None

    # ── 日志 ──────────────────────────────────────────────────────
    def _log_start(self, module: str):
        print(f"🚀 [{module}] 开始爬取(浏览器)...")

    def _log_done(self, module: str, count: int):
        print(f"✅ [{module}] 爬取完成，共 {count} 条")

    def _log_save(self, module: str, count: int):
        print(f"💾 [{module}] 保存成功，共 {count} 条")

    def _log_skip(self, module: str, reason: str = ""):
        print(f"⏭️  [{module}] 跳过: {reason}" if reason else f"⏭️  [{module}] 跳过")
