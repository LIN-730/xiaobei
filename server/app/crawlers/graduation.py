# crawlers/graduation.py — 毕业审核结果核查 (GNMKDM: N105508)
# ⚠️ NEEDS_BROWSER: 该模块使用正方教务Grid组件，需要浏览器JS初始化。
from typing import List, Dict, Any, Optional
from crawlers.base import BaseCrawler


class GraduationCrawler(BaseCrawler):
    """
    爬取毕业审核结果。⚠️ 需要浏览器自动化。
    GNMKDM: N105508
    """
    GNMKDM = "N105508"
    TABLE_NAME = "GraduationAudit"

    def crawl(self) -> Optional[List[Dict[str, Any]]]:
        self._log_skip("毕业审核", "需要浏览器自动化（Playwright），待Phase 2实现")
        return None

    def save_to_db(self, data: List[Dict]) -> int:
        return 0
