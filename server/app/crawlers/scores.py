# crawlers/scores.py — 成绩爬虫, 全学期 (GNMKDM: N305005)
import time
from typing import List, Dict, Any, Optional
from crawlers.base import BaseCrawler
from database import replace_table_data, compute_sync_hash
from user_profile import xqm_to_term_name


class ScoreCrawler(BaseCrawler):
    """爬取所有学期成绩。xnm='' xqm='' 即可返回全部。"""

    API_PATH = "/jwglxt/cjcx/cjcx_cxXsgrcj.html"
    GNMKDM = "N305005"
    TABLE_NAME = "Score"

    def crawl(self) -> Optional[List[Dict[str, Any]]]:
        self._log_start("成绩")
        post_data = {
            "xnm": "", "xqm": "", "_search": "false",
            "nd": int(time.time() * 1000),
            "queryModel.showCount": "500",
            "queryModel.currentPage": "1",
            "queryModel.sortName": "", "queryModel.sortOrder": "asc",
            "time": "0",
        }
        resp = self._post_api(self.API_PATH, data=post_data,
                              gnmkdm=self.GNMKDM, extra_params="doType=query")
        data = self._safe_json(resp, "成绩")
        if not data: return []

        items = data.get("items") or data.get("result") or data.get("list") or []
        result = []
        for item in items:
            if not isinstance(item, dict): continue
            xnm = item.get("xnm", ""); xqm = item.get("xqm", "")
            term = xqm_to_term_name(xnm, xqm) if xnm else ""
            row = {
                "StudentNo": self.student_no, "Term": term,
                "CourseName": item.get("kcmc", ""),
                "CourseCode": item.get("kcdm", ""),
                "Score": str(item.get("cj", "")),
                "Credit": float(item.get("xf", 0) or 0),
                "GradePoint": float(item.get("jd", 0) or 0),
                "CourseType": item.get("kcxzmc", ""),
                "ExamType": item.get("ksxz", ""),
            }
            row["SyncHash"] = compute_sync_hash(row)
            result.append(row)

        self._log_done("成绩", len(result))
        return result

    def save_to_db(self, data: List[Dict]) -> int:
        return replace_table_data(self.TABLE_NAME, self.student_no, data)
