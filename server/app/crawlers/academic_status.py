# crawlers/academic_status.py — 学业情况, JS源码解析 (GNMKDM: N105515)
# 数据在页面<script>中的JS模板字符串里, 不是HTML DOM
import re
from typing import Dict, Any, Optional
from crawlers.base import BaseCrawler
from database import get_db_conn


class AcademicStatusCrawler(BaseCrawler):
    PAGE_PATH = "/jwglxt/xsxy/xsxyqk_cxXsxyqkIndex.html"
    GNMKDM = "N105515"

    def crawl(self) -> Optional[Dict[str, Any]]:
        self._log_start("学业情况")
        url = f"{self.base_url}{self.PAGE_PATH}?gnmkdm={self.GNMKDM}&layout=default"
        resp = self.session.get(url, timeout=15)
        if resp.status_code != 200:
            print(f"  HTTP {resp.status_code}"); return None

        html = resp.text
        result = {"StudentNo": self.student_no}

        # ── 总体汇总 ──
        # 模式: "专业名&nbsp;要求学分:176.0&nbsp;获得学分:91.0&nbsp;未获得学分:85.0"
        m = re.search(r'"(\d{4}\S+?)&nbsp;".*?要求学分.*?:([\d.]+).*?获得学分.*?:([\d.]+).*?未获得学分.*?:([\d.]+)', html)
        if m:
            result["Major"] = m.group(1)
            result["TotalCredits"] = float(m.group(2))
            result["EarnedCredits"] = float(m.group(3))
            result["FailedCredits"] = float(m.group(4))

        # ── GPA (在<font>标签内) ──
        m = re.search(r'GPA[）)].*?<font[^>]*>\s*([\d.]+)', html, re.DOTALL)
        if m: result["AverageGPA"] = float(m.group(1))

        # ── 课程总数（处理 &nbsp; 和 HTML注释） ──
        m = re.search(r'计划总课程.*?(\d+).*?门', html, re.DOTALL)
        if m: result["TotalCourses"] = int(m.group(1))

        label_patterns = [
            ("通过", "Passed"), ("未通过", "Failed"),
            ("未修", "NotTaken"), ("在读", "InProgress"),
        ]
        for label, key in label_patterns:
            m = re.search(rf'{label}.*?(\d+).*?门', html, re.DOTALL)
            if m: result[key] = int(m.group(1))

        # ── 按模块组: yqzdxf='X' 前有模块名 ──
        modules = []
        # 找出所有 "模块名&nbsp;要求学分:X&nbsp;获得学分:Y&nbsp;未获得学分:Z"
        mod_pattern = re.compile(
            r'"(\S+?)&nbsp;".*?'
            r'要求学分.*?:([\d.]+)&nbsp;".*?'
            r'获得学分.*?:([\d.]+)&nbsp;.*?'
            r'未获得学分.*?:([\d.]+)&nbsp;'
        )
        for m in mod_pattern.finditer(html):
            name = m.group(1)
            if name == result.get("Major", ""): continue  # skip summary
            modules.append({
                "name": name,
                "required": float(m.group(2)),
                "earned": float(m.group(3)),
                "remaining": float(m.group(4)),
            })

        # 补充门次信息: "要求门次:X 到达要求:Y 未达到要求:Z"
        req_pattern = re.compile(r'要求门次[：:]\s*(\d+)\s+到达要求[：:]\s*(\d+)\s+未达到要求[：:]\s*(\d+)')
        for i, m in enumerate(req_pattern.finditer(html)):
            if i < len(modules):
                modules[i]["requiredCount"] = int(m.group(1))
                modules[i]["metCount"] = int(m.group(2))
                modules[i]["unmetCount"] = int(m.group(3))

        # 补充课程数量: "共（N）门 通过（M）门"
        cnt_pattern = re.compile(r'共[（(]\s*(\d+)\s*门\s*[）)]\s*通过[（(]\s*(\d+)\s*门')
        for i, m in enumerate(cnt_pattern.finditer(html)):
            if i < len(modules):
                modules[i]["totalCount"] = int(m.group(1))
                modules[i]["passedCount"] = int(m.group(2))

        # ── 去重（JS模板对每个模块生成了两份） ──
        seen = set()
        unique_modules = []
        for m in modules:
            key = f"{m['name']}-{m['required']}-{m['earned']}"
            if key not in seen:
                seen.add(key)
                unique_modules.append(m)

        result["ModuleDetails"] = str(unique_modules)
        result["ModuleCount"] = len(unique_modules)

        self._log_done("学业情况", 1)
        return result

    def save_to_db(self, data) -> int:
        if not data: return 0
        conn = get_db_conn(); cur = conn.cursor()
        try:
            cur.execute("DELETE FROM AcademicStatus WHERE StudentNo=?", (self.student_no,))
            cur.execute("""INSERT INTO AcademicStatus
                (StudentNo, TotalCredits, EarnedCredits, FailedCredits, AverageGPA, RawData)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (self.student_no, data.get("TotalCredits", 0),
                 data.get("EarnedCredits", 0), data.get("FailedCredits", 0),
                 data.get("AverageGPA", 0), str(data.get("ModuleDetails", ""))))
            conn.commit(); return 1
        except Exception as e:
            print(f"  DB: {e}"); conn.rollback(); return 0
        finally: cur.close(); conn.close()
