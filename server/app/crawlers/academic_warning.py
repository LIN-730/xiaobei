# crawlers/academic_warning.py — 学籍预警查询 (GNMKDM: N105505)
from typing import List, Dict, Any, Optional
from crawlers.base import BaseCrawler
from database import replace_table_data


class AcademicWarningCrawler(BaseCrawler):
    """
    爬取学籍预警信息。
    页面: /xjyj/xjyj_cxXjyjIndex.html
    GNMKDM: N105505
    """

    # 数据API路径（通常不带Index后缀）
    API_CANDIDATES = [
        "/jwglxt/xjyj/xjyj_cxXjyj.html",
        "/jwglxt/xjyj/xjyj_cxXjyjIndex.html",
    ]
    GNMKDM = "N105505"
    TABLE_NAME = "AcademicWarning"

    def crawl(self) -> Optional[List[Dict[str, Any]]]:
        self._log_start("学籍预警")

        # 尝试多个路径
        data = None
        for path in self.API_CANDIDATES:
            resp = self._post_api(path, data={}, gnmkdm=self.GNMKDM)
            data = self._safe_json(resp, "学籍预警")
            if data and not isinstance(data, str):
                print(f"   ✅ 路径有效: {path}")
                break

        if not data:
            # 探针模式分析响应
            data = self._probe_api(
                self.API_CANDIDATES[0], data={},
                gnmkdm=self.GNMKDM, module_name="学籍预警",
            )
        if not data:
            return []

        # 解析列表
        items = (data.get("items") or data.get("rows") or
                 data.get("list") or data.get("result") or [])
        if isinstance(data, list):
            items = data

        result = []
        for item in items:
            if not isinstance(item, dict):
                continue
            result.append({
                "StudentNo": self.student_no,
                "WarningType": item.get("yjmc", "") or item.get("warningType", ""),
                "WarningLevel": item.get("yjjb", "") or item.get("warningLevel", ""),
                "Description": item.get("yjnr", "") or item.get("description", ""),
                "CreateTime": item.get("cjsj", "") or item.get("createTime", ""),
                "Status": item.get("zt", "") or item.get("status", ""),
            })

        self._log_done("学籍预警", len(result))
        return result

    def save_to_db(self, data: List[Dict]) -> int:
        return replace_table_data(self.TABLE_NAME, self.student_no, data)


if __name__ == "__main__":
    from crawlers.auth import login_edu
    sess = login_edu()
    if sess:
        c = AcademicWarningCrawler(sess)
        data = c.crawl()
        if data:
            print(f"\n共 {len(data)} 条预警")
