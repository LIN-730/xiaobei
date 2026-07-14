# crawlers/exams.py — 考试爬虫, 全学期 (GNMKDM: N358105)
from typing import List, Dict, Any, Optional
from crawlers.base import BaseCrawler
from database import replace_table_data
from user_profile import generate_semester_list


class ExamCrawler(BaseCrawler):
    """爬取所有学期考试安排。xnm='' xqm='' 返回全部。"""

    API_PATH = "/jwglxt/kwgl/kscx_cxXsksxxIndex.html"
    GNMKDM = "N358105"
    TABLE_NAME = "Exam"

    # 先空参数查全部，再逐学期查（动态生成，不硬编码年份）
    SEMESTERS = [("", "")] + generate_semester_list(years_back=2)

    def crawl(self) -> Optional[List[Dict[str, Any]]]:
        self._log_start("考试安排")

        # Try all-semesters first, then individual
        all_items = {}
        for xnm, xqm in self.SEMESTERS:
            post_data = {"xnm": xnm, "xqm": xqm,
                         "ksmcdmb_id": "", "kch": "", "kc": "",
                         "ksrq": "", "kkbm_id": ""}
            resp = self._post_api(self.API_PATH, data=post_data,
                                  gnmkdm=self.GNMKDM, extra_params="doType=query")
            data = self._safe_json(resp, "考试安排")
            if not data: continue
            items = data.get("items") or []
            for item in items:
                if not isinstance(item, dict): continue
                k = f"{item.get('kcmc','')}-{item.get('kssj','')}"
                if k not in all_items:
                    all_items[k] = item

        result = []
        for item in all_items.values():
            result.append({
                "StudentNo": item.get("xh_id", self.student_no),
                "CourseName": item.get("kcmc", ""),
                "ExamDate": item.get("kssj", ""),
                "ExamTime": item.get("sksj", ""),
                "Classroom": item.get("cdmc", ""),
                "SeatNo": str(item.get("zwh", "")),
                "ExamType": item.get("ksmc", "") or item.get("ksfs", ""),
                "Campus": item.get("cdxqmc", "") or item.get("xqmc", ""),
            })

        self._log_done("考试安排", len(result))
        return result

    def save_to_db(self, data: List[Dict]) -> int:
        return replace_table_data(self.TABLE_NAME, self.student_no, data)
