# crawlers/courses.py — 个人课表爬虫, 遍历所有学期 (GNMKDM: N2151)
import re
from typing import List, Dict, Any, Optional
from crawlers.base import BaseCrawler
from database import replace_table_data, compute_sync_hash
from user_profile import generate_semester_list, xqm_to_term_name


class CourseCrawler(BaseCrawler):
    """遍历所有学年学期爬取全部课表"""

    API_PATH = "/jwglxt/kbcx/xskbcx_cxXsKb.html"
    GNMKDM = "N2151"
    TABLE_NAME = "Course"

    # 学期列表由 generate_semester_list() 动态生成（避免硬编码随时间失效）
    SEMESTERS = generate_semester_list(years_back=2)

    def crawl(self) -> Optional[List[Dict[str, Any]]]:
        self._log_start("课表")
        all_rows = []
        zcd_pattern = re.compile(r"\([^)]*\)")

        for xnm, xqm in self.SEMESTERS:
            resp = self._post_api(self.API_PATH, data={"xnm": xnm, "xqm": xqm},
                                  gnmkdm=self.GNMKDM)
            data = self._safe_json(resp, f"课表({xnm}-{xqm})")
            if not data or "kbList" not in data or not data["kbList"]:
                continue

            for item in data["kbList"]:
                jc = item.get("jcs", "1-1").split("-")
                zcd_clean = zcd_pattern.sub("", item.get("zcd", "").replace("周", ""))
                for seg in zcd_clean.split(","):
                    seg = seg.strip()
                    if not seg: continue
                    wr = seg.split("-")
                    sw = int(wr[0])
                    ew = int(wr[-1]) if len(wr) > 1 else sw
                    xnm_val = item.get("xnm", xnm)
                    xqm_val = item.get("xqm", xqm)
                    term = xqm_to_term_name(xnm_val, xqm_val)
                    row = {
                        "StudentNo": self.student_no,
                        "CourseCode": item.get("kcdm", ""),
                        "CourseName": item.get("kcmc", ""),
                        "Teacher": item.get("xm", ""),
                        "TeacherTitle": item.get("jszc", ""),
                        "Classroom": item.get("cdmc", ""),
                        "Campus": item.get("xqmc", ""),
                        "Building": item.get("jxlmc", ""),
                        "WeekDay": int(item.get("xqj", 0)),
                        "StartNode": int(jc[0]), "EndNode": int(jc[-1]),
                        "StartWeek": sw, "EndWeek": ew,
                        "WeekInfo": item.get("zcd", ""),
                        "Credit": float(item.get("xf", 0) or 0),
                        "CourseType": item.get("kcxz", ""),
                        "Term": term,
                        "xnm": xnm_val, "xqm": xqm_val,
                    }
                    row["SyncHash"] = compute_sync_hash(row)
                    all_rows.append(row)

        self._log_done("课表", len(all_rows))
        return all_rows

    def save_to_db(self, data: List[Dict]) -> int:
        return replace_table_data(self.TABLE_NAME, self.student_no, data)
