# crawlers/score_detail.py — 成绩明细, Grid API (GNMKDM: N305007)
# API: /cjcx/cjcx_cxXsKccjList.html?doType=query (从页面JS cxDgXsxmcj.js提取)
from typing import List, Dict, Any, Optional
from crawlers.base import BaseCrawler
from database import replace_table_data
from user_profile import xqm_to_term_name


class ScoreDetailCrawler(BaseCrawler):
    """爬取成绩明细——每门课的单项成绩和权重"""

    API_PATH = "/jwglxt/cjcx/cjcx_cxXsKccjList.html"
    GNMKDM = "N305007"
    TABLE_NAME = "ScoreDetail"

    def crawl(self) -> Optional[List[Dict[str, Any]]]:
        self._log_start("成绩明细")

        import time
        resp = self._post_api(self.API_PATH,
                              data={"xnm": "", "xqm": "", "_search": "false",
                                    "nd": int(time.time()*1000),
                                    "queryModel.showCount": "500",
                                    "queryModel.currentPage": "1"},
                              gnmkdm=self.GNMKDM,
                              extra_params="doType=query")
        data = self._safe_json(resp, "成绩明细")
        if not data: return []

        items = data.get("items") or []
        result = []
        for item in items:
            if not isinstance(item, dict): continue
            xnm = item.get("xnm", ""); xqm = item.get("xqm", "")
            term = xqm_to_term_name(xnm, xqm) if xnm else ""
            result.append({
                "StudentNo": item.get("xh_id", self.student_no),
                "CourseName": item.get("kcmc", ""),
                "CourseCode": item.get("kch", ""),
                "Credit": float(item.get("xf", 0) or 0),
                "Score": str(item.get("xmcj", "")),     # 项目成绩
                "GradePoint": 0,
                "CourseType": item.get("xmblmc", ""),    # 项目比例名称(平时/期末/实验等)
                "ExamType": item.get("jxbmc", ""),       # 教学班名称
                "Term": term,
            })

        self._log_done("成绩明细", len(result))
        return result

    def save_to_db(self, data: List[Dict]) -> int:
        return replace_table_data(self.TABLE_NAME, self.student_no, data)
