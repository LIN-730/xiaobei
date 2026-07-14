# tools/gpa_tools.py — GPA 模拟器 (P6.1)
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.repositories.repos import AcademicStatusRepo


# 北化百分制 → 绩点映射表
def score_to_gp(score: float) -> float:
    """将百分制分数转换为绩点（北化标准）"""
    if score >= 95:
        return 4.33
    if score >= 90:
        return 4.0
    if score >= 85:
        return 3.7
    if score >= 82:
        return 3.3
    if score >= 78:
        return 3.0
    if score >= 75:
        return 2.7
    if score >= 72:
        return 2.3
    if score >= 68:
        return 2.0
    if score >= 64:
        return 1.5
    if score >= 60:
        return 1.0
    return 0.0


GP_LEVELS = [
    (4.33, "95-100", "A+"),
    (4.0, "90-94", "A"),
    (3.7, "85-89", "A-"),
    (3.3, "82-84", "B+"),
    (3.0, "78-81", "B"),
    (2.7, "75-77", "B-"),
    (2.3, "72-74", "C+"),
    (2.0, "68-71", "C"),
    (1.5, "64-67", "C-"),
    (1.0, "60-63", "D"),
    (0.0, "0-59", "F"),
]


async def simulate_gpa(
    db: AsyncSession,
    user_id: str,
    courses_json: str,
) -> str:
    """
    模拟计算 GPA：输入预估课程列表，输出模拟后的 GPA 及变化。
    参数: courses_json (JSON字符串, 格式 [{"name":"课程名","credit":3.0,"score":90}, ...])
    最多支持 10 门课同时模拟。
    触发: 「如果我高数考90分GPA多少」「模拟GPA」「绩点计算」等。
    """
    import json

    try:
        courses = json.loads(courses_json)
    except (json.JSONDecodeError, TypeError):
        return "参数格式错误。请提供 JSON 数组，如：[{\"name\":\"高数\",\"credit\":4.0,\"score\":90}]"

    if not isinstance(courses, list) or len(courses) == 0:
        return "请至少提供一门课程进行模拟。"
    if len(courses) > 10:
        return "最多同时模拟 10 门课程。"

    # 获取当前学业状态
    repo = AcademicStatusRepo(db, user_id)
    status = await repo.get_status()

    if not status:
        return "暂无学业数据，请先同步教务数据。"

    current_credits = float(status.earned_credits or 0)
    current_gpa_sum = float(status.gpa_sum or 0)
    current_gpa = float(status.average_gpa or 0)

    # 计算模拟课程
    sim_details = []
    sim_gp_sum = 0.0
    sim_credits = 0.0
    errors = []

    for i, c in enumerate(courses):
        name = c.get("name", f"课程{i + 1}")
        try:
            credit = float(c.get("credit", 0))
            score = float(c.get("score", 0))
        except (ValueError, TypeError):
            errors.append(f"{name}: 学分和分数需为有效数字")
            continue

        if credit <= 0:
            errors.append(f"{name}: 学分必须大于0")
            continue
        if score < 0 or score > 100:
            errors.append(f"{name}: 分数需在0-100之间")
            continue

        gp = score_to_gp(score)
        sim_details.append({
            "name": name,
            "credit": credit,
            "score": score,
            "grade_point": gp,
            "gp_contribution": round(gp * credit, 2),
        })
        sim_gp_sum += gp * credit
        sim_credits += credit

    if errors:
        return "输入错误：\n" + "\n".join(f"  - {e}" for e in errors)

    # 计算模拟后 GPA
    new_total_credits = current_credits + sim_credits
    new_gpa_sum = current_gpa_sum + sim_gp_sum
    new_gpa = round(new_gpa_sum / new_total_credits, 2) if new_total_credits > 0 else 0.0
    gpa_change = round(new_gpa - current_gpa, 2)

    # 格式化输出
    change_str = f"+{gpa_change}" if gpa_change > 0 else str(gpa_change)
    arrow = "📈" if gpa_change > 0 else ("📉" if gpa_change < 0 else "➡️")

    result = f"🧮 GPA 模拟结果 {arrow}\n\n"
    result += f"当前 GPA: {current_gpa} (已修 {current_credits} 学分)\n"
    result += f"模拟后 GPA: {new_gpa} (新增 {sim_credits} 学分, 变化 {change_str})\n\n"
    result += "模拟课程明细：\n"

    for d in sim_details:
        result += f"  {d['name']}: {d['score']}分 → 绩点{d['grade_point']} × {d['credit']}学分 = {d['gp_contribution']}\n"

    # 绩点对照表
    result += "\n📋 绩点对照参考：\n"
    for gp, score_range, grade in GP_LEVELS:
        result += f"  {grade}  {gp:.2f}  ←  {score_range}分\n"

    return result
