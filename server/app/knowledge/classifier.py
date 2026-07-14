# app/knowledge/classifier.py — LLM智能分类器
"""根据文件内容自动分类到预定义类别"""
import re
from typing import Dict, Optional


# 分类体系
CATEGORIES = {
    "培养方案": ["培养方案", "教学计划", "课程设置", "学分要求", "毕业要求",
                 "专业必修", "通识教育", "实践环节", "选修课"],
    "课程资料": ["课程大纲", "教学大纲", "课件", "讲义", "教材", "实验指导",
                 "习题", "作业", "考试大纲", "复习", "syllabus"],
    "考试资料": ["考试安排", "准考证", "考场", "成绩单", "补考", "缓考"],
    "通知公告": ["通知", "公告", "教务处", "选课通知", "注册", "报到",
                 "放假", "开学", "考试周"],
    "个人文件": ["简历", "申请", "证明", "在读证明", "成绩证明", "学籍"],
    "课件PPT": [".ppt", "幻灯片", "presentation"],
    "其他": [],
}


def classify_by_keywords(text: str, filename: str = "") -> str:
    """
    基于关键词的快速分类（无需LLM）。
    优先匹配中文关键词，回退到文件扩展名。
    """
    text_lower = text.lower()[:3000]  # 只看前3000字符
    filename_lower = filename.lower()
    scores = {}

    for cat, keywords in CATEGORIES.items():
        score = 0
        for kw in keywords:
            if kw.lower() in text_lower:
                score += 2  # 内容匹配权重高
            if kw.lower() in filename_lower:
                score += 1  # 文件名匹配
        scores[cat] = score

    # 返回得分最高的类别
    best = max(scores, key=scores.get)
    if scores[best] > 0:
        return best

    # 回退：根据扩展名
    ext_map = {".pdf": "课程资料", ".docx": "课程资料", ".doc": "课程资料",
               ".xlsx": "个人文件", ".xls": "个人文件",
               ".pptx": "课件PPT", ".ppt": "课件PPT",
               ".txt": "其他", ".md": "其他"}
    ext = filename_lower[filename_lower.rfind("."):] if "." in filename_lower else ""
    return ext_map.get(ext, "其他")


def classify_with_llm(text: str, filename: str = "",
                       llm=None) -> Dict:
    """
    使用LLM进行精细分类（需要传入已初始化的LLM实例）。
    返回 {"category": str, "sub_category": str, "tags": [...], "summary": str}
    """
    if llm is None:
        cat = classify_by_keywords(text, filename)
        return {"category": cat, "sub_category": "", "tags": [], "summary": text[:200]}

    prompt = f"""分析以下文档内容，返回JSON格式分类结果：

文档名: {filename}
内容片段（前2000字）:
{text[:2000]}

请返回：
{{
  "category": "培养方案/课程资料/考试资料/通知公告/个人文件/课件PPT/其他",
  "sub_category": "细分类别（如'专业必修'/'期末试卷'等）",
  "tags": ["标签1", "标签2", "标签3"],
  "summary": "一句话概括（不超过50字）"
}}"""

    try:
        from langchain_core.messages import HumanMessage
        resp = llm.invoke([HumanMessage(content=prompt)])
        import json
        result = json.loads(resp.content)
        return result
    except Exception:
        return {"category": classify_by_keywords(text, filename),
                "sub_category": "", "tags": [], "summary": text[:200]}


def extract_course_names(text: str) -> list:
    """从文本中提取可能的课程名"""
    patterns = [
        r'《([^》]+）》',                          # 《高等数学》
        r'"([^"]+)"\s*(?:课程|课)',               # "高等数学"课程
        r'课程名称[：:]\s*(\S+)',                  # 课程名称：高等数学
        r'([一-龥]+(?:数学|物理|化学|英语|程序设计|实验|实习|概论|原理|导论|技术))',
    ]
    courses = set()
    for p in patterns:
        for m in re.finditer(p, text):
            name = m.group(1).strip()
            if 2 <= len(name) <= 30:
                courses.add(name)
    return list(courses)[:10]
