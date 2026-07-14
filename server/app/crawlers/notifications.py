# crawlers/notifications.py — 主页通知/文件/消息爬虫
"""
三个板块均走 Grid API: POST pageURL?doType=query → JSON
来源: 主页 index_initMenu.html 自动触发的 POST 请求
"""
import re, time
from typing import List, Dict, Any, Optional
from crawlers.base import BaseCrawler
from database import get_db_conn


class NotificationCrawler(BaseCrawler):
    """
    爬取主页三大板块: 通知/文件/消息
    表: Notifications (category区分)
    """

    MODULES = {
        "通知": {
            "path": "/jwglxt/xtgl/xwck_cxMoreXwList.html",
            "fields": ["category","tag","title","content","date","link"],
        },
        "文件": {
            "path": "/jwglxt/xtgl/xwck_cxMoreWjList.html",
            "fields": ["category","tag","title","filename","publisher","date","hash_link"],
        },
        "消息": {
            "path": "/jwglxt/xtgl/index_cxDbsy.html",
            "fields": ["category","title","content","role","date","status"],
        },
    }

    def crawl(self) -> Dict[str, List[Dict]]:
        """爬取全部三个板块，返回 {category: [items]}"""
        all_data = {}
        for category, cfg in self.MODULES.items():
            self._log_start(category)
            items = self._fetch_all_pages(cfg["path"], category)
            all_data[category] = items
            self._log_done(category, len(items))
        return all_data

    def _fetch_all_pages(self, path: str, category: str) -> List[Dict]:
        """分页拉取全部数据"""
        all_items = []
        page = 1
        while True:
            resp = self._post_api(
                path, data={
                    "queryModel.showCount": "500",
                    "queryModel.currentPage": str(page),
                },
                extra_params="doType=query",
            )
            data = self._safe_json(resp, category)
            if not data:
                break

            items = data.get("items") or []
            if not items:
                break

            for item in items:
                parsed = self._parse_item(item, category)
                if parsed:
                    all_items.append(parsed)

            total = int(data.get("totalResult", 0))
            if len(all_items) >= total:
                break
            page += 1

        return all_items

    def _parse_item(self, item: Dict, category: str) -> Optional[Dict]:
        base = {"category": category}
        if category == "通知":
            content = item.get("fbnr", "")  # HTML content
            title = item.get("fbbt", "") or item.get("xwbt", "")
            clean_title = re.sub(r'<[^>]+>', '', title or "")
            base.update({
                "tag": item.get("sfzd", "") or "",
                "title": clean_title or self._extract_text(content)[:100],
                "content": self._extract_text(content),
                "date": item.get("fbsj", "") or item.get("cjsj", ""),
            })
        elif category == "文件":
            base.update({
                "tag": item.get("sfzd", "") or "",
                "title": item.get("fjm", "") or item.get("wjm", ""),
                "filename": item.get("fjm", ""),
                "publisher": item.get("fbr", ""),
                "date": item.get("fbsj", ""),
                "hash_link": item.get("fjsclj", ""),
            })
        elif category == "消息":
            base.update({
                "title": item.get("xxmc", "") or item.get("xxbt", ""),
                "content": item.get("xxnr", "") or "",
                "role": item.get("jsmc", ""),
                "date": item.get("cjsj", ""),
                "status": item.get("clzt", ""),
            })
        return base

    def _extract_text(self, html: str) -> str:
        return re.sub(r'<[^>]+>', '', html or "").strip()

    def save_to_db(self, data: Dict[str, List]) -> Dict[str, int]:
        if not data: return {}
        conn = get_db_conn()
        cur = conn.cursor()
        counts = {}
        try:
            cur.execute("DELETE FROM Notifications")
            for category, items in data.items():
                for item in items:
                    cur.execute(
                        """INSERT INTO Notifications
                        (category, tag, title, content, date, link)
                        VALUES (?, ?, ?, ?, ?, ?)""",
                        (category,
                         str(item.get("tag", "")),
                         str(item.get("title", "")),
                         str(item.get("content", ""))[:5000],
                         str(item.get("date", "")),
                         str(item.get("hash_link", ""))))
                counts[category] = len(items)
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"  [通知] DB error: {e}")
        finally:
            cur.close(); conn.close()
        return counts


if __name__ == "__main__":
    from crawlers.auth import login_edu
    sess = login_edu()
    if sess:
        c = NotificationCrawler(sess)
        data = c.crawl()
        for cat, items in data.items():
            print(f"\n{cat}: {len(items)}条")
            for item in items[:3]:
                print(f"  [{item.get('date','')}] {item.get('title','')[:80]}")
        c.save_to_db(data)
