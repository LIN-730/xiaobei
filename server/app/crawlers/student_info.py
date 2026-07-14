# crawlers/student_info.py — 个人信息 HTML解析 (GNMKDM: N100801)
# 页面: /xsxxxggl/xsgrxxwh_cxXsgrxx.html (非Index!)
# 数据在HTML的 div/table 中以 label-value 对出现
import re
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
from crawlers.base import BaseCrawler
from database import get_db_conn


class StudentInfoCrawler(BaseCrawler):
    PAGE_PATH = "/jwglxt/xsxxxggl/xsgrxxwh_cxXsgrxx.html"
    GNMKDM = "N100801"

    # 页面标签→DB字段映射
    FIELD_MAP = {
        "学号": "StudentNo", "姓名": "Name", "性别": "Gender",
        "姓名拼音": "Pinyin", "英文姓名": "EnglishName",
        "学院名称": "College", "所属学院": "College",
        "专业名称": "Major", "班级名称": "ClassName",
        "年级": "Grade", "学制": "EduLevel", "校区": "Campus",
        "学籍状态": "Status", "出生日期": "BirthDate", "民族": "Nation",
        "生源地": "Origin", "入学日期": "EnrollDate",
        "电子邮箱": "Email", "手机号码": "Phone",
        "家庭地址": "Address", "家庭电话": "HomePhone",
        "证件类型": "IDType", "证件号码": "IDNumber",
        "火车票区间站": "TrainStation",
        "专业方向": "MajorDirection",
    }

    def crawl(self) -> Optional[Dict[str, Any]]:
        self._log_start("个人信息")
        url = f"{self.base_url}{self.PAGE_PATH}?gnmkdm={self.GNMKDM}"
        resp = self.session.get(url, timeout=15)

        if resp.status_code != 200:
            print(f"  HTTP {resp.status_code}"); return None

        soup = BeautifulSoup(resp.text, "html.parser")
        info = {"StudentNo": self.student_no}

        # 方法1: 从表格行提取 th/td
        for row in soup.select("tr"):
            cells = [c.get_text(strip=True) for c in row.find_all(["th", "td"])]
            for i in range(len(cells) - 1):
                k = cells[i].rstrip("：:")
                if k in self.FIELD_MAP and cells[i + 1]:
                    info[self.FIELD_MAP[k]] = cells[i + 1]

        # 方法2: 从 div.form-group / div.row 提取
        for div in soup.select("div.form-group, div.row, div.col-md-"):
            labels = div.select("label")
            if len(labels) == 1:
                k = labels[0].get_text(strip=True).rstrip("：:")
                v = div.get_text(strip=True).replace(k, "", 1).lstrip("：:")
                if k in self.FIELD_MAP and v and self.FIELD_MAP[k] not in info:
                    info[self.FIELD_MAP[k]] = v

        # 方法3: 纯文本正则匹配 (后备)
        text = soup.get_text(" ", strip=True)
        for label, col in self.FIELD_MAP.items():
            if col not in info or not info[col]:
                m = re.search(re.escape(label) + r'\s*[：:]\s*(\S+)', text)
                if m:
                    val = m.group(1).strip()
                    if val and len(val) < 50:
                        info[col] = val

        # 方法4: 多行模式 - 标签和值在不同行
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        for i, line in enumerate(lines):
            for label, col in self.FIELD_MAP.items():
                if line == label or line.startswith(label + "："):
                    if i + 1 < len(lines):
                        val = lines[i + 1].strip()
                        if val and len(val) < 100 and col not in info:
                            info[col] = val

        self._log_done("个人信息", 1)
        return info

    def save_to_db(self, data) -> int:
        if not data: return 0
        conn = get_db_conn(); cur = conn.cursor()
        try:
            cur.execute("DELETE FROM Student WHERE StudentNo=?", (self.student_no,))
            cols = ["StudentNo","Name","Gender","College","Major","ClassName",
                    "Grade","Campus","EduLevel","RawData"]
            cur.execute(
                f"INSERT INTO Student ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})",
                [str(data.get(c, "")) for c in cols])
            conn.commit()
            return 1
        except Exception as e:
            print(f"  DB error: {e}"); conn.rollback(); return 0
        finally: cur.close(); conn.close()
