# crawlers/all_courses.py — 全校课表查询 (GNMKDM: N219933)
import re
from typing import List, Dict, Any, Optional
from crawlers.base import BaseCrawler
from user_profile import get_current_semester, xqm_to_term_name


class AllCoursesCrawler(BaseCrawler):
    """
    查询全校课表。使用与个人课表相同的API但不同GNMKDM。
    API: /kbcx/xskbcx_cxXsKb.html?gnmkdm=N219933
    """

    API_PATH = "/jwglxt/kbcx/xskbcx_cxXsKb.html"
    GNMKDM = "N219933"

    def crawl(self, xnm: str = None, xqm: str = None) -> Optional[List[Dict[str, Any]]]:
        if xnm is None or xqm is None:
            sem = get_current_semester()
            xnm = sem['xnm']
            xqm = sem['xqm']
        self._log_start("全校课表")
        term = xqm_to_term_name(xnm, xqm)
        zcd_pattern = re.compile(r"\([^)]*\)")
        result = []

        resp = self._post_api(self.API_PATH, data={"xnm": xnm, "xqm": xqm},
                              gnmkdm=self.GNMKDM)
        data = self._safe_json(resp, "全校课表")
        if not data or "kbList" not in data: return []

        for item in data["kbList"]:
            jc = item.get("jcs", "1-1").split("-")
            zcd_clean = zcd_pattern.sub("", item.get("zcd", "").replace("周", ""))
            for seg in zcd_clean.split(","):
                seg = seg.strip()
                if not seg: continue
                wr = seg.split("-")
                result.append({
                    "StudentNo": "",
                    "CourseCode": item.get("kcdm", ""),
                    "CourseName": item.get("kcmc", ""),
                    "Teacher": item.get("xm", ""),
                    "Classroom": item.get("cdmc", ""),
                    "Campus": item.get("xqmc", ""),
                    "Building": item.get("jxlmc", ""),
                    "WeekDay": int(item.get("xqj", 0)),
                    "StartNode": int(jc[0]), "EndNode": int(jc[-1]),
                    "StartWeek": int(wr[0]),
                    "EndWeek": int(wr[-1]) if len(wr) > 1 else int(wr[0]),
                    "WeekInfo": item.get("zcd", ""),
                    "Credit": float(item.get("xf", 0) or 0),
                    "CourseType": item.get("kcxz", ""),
                    "Term": term, "xnm": xnm, "xqm": xqm,
                })

        self._log_done("全校课表", len(result))
        return result

    def save_to_db(self, data: List[Dict]) -> int:
        from database import get_db_conn
        if not data: return 0
        conn = get_db_conn(); cur = conn.cursor()
        try:
            cur.execute("DELETE FROM Course WHERE StudentNo=''")
            cols = list(data[0].keys()); ph = ",".join(["?"]*len(cols))
            sql = f"INSERT INTO Course ({','.join(cols)}) VALUES ({ph})"
            for r in data: cur.execute(sql, [r.get(c,"") for c in cols])
            conn.commit(); return len(data)
        except Exception as e:
            conn.rollback(); print(f"  [全校课表] DB error: {e}"); return 0
        finally: cur.close(); conn.close()
