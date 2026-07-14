# tools/__init__.py — Tool 工厂 (P3)
"""
将所有异步查询函数包装为 LangChain Tool。
每个 Tool 的 coroutine 通过闭包绑定 db + user_id。

用法:
    tools = create_tools(db, user_id, student_no, rag_manager=None)
    # → list[BaseTool]
"""
from __future__ import annotations

from typing import Optional

from langchain_core.tools import StructuredTool
from sqlalchemy.ext.asyncio import AsyncSession

# 导入所有 Tool 函数
from app.agent.tools.course_tools import query_courses as _query_courses
from app.agent.tools.score_tools import query_scores as _query_scores
from app.agent.tools.exam_tools import query_exams as _query_exams
from app.agent.tools.student_tools import (
    query_student_info as _query_student_info,
    query_academic_status as _query_academic_status,
    query_warnings as _query_warnings,
)
from app.agent.tools.training_tools import (
    query_training_plan as _query_training_plan,
    query_selected_courses as _query_selected_courses,
    query_classrooms as _query_classrooms,
)
from app.agent.tools.planning_tools import (
    analyze_credit_gap as _analyze_credit_gap,
    check_required_courses as _check_required_courses,
    recommend_courses as _recommend_courses,
    plan_academic_path as _plan_academic_path,
)
from app.agent.tools.knowledge_tools import create_knowledge_tools
from app.agent.tools.gpa_tools import simulate_gpa as _simulate_gpa
from app.agent.tools.conflict_tools import detect_course_conflicts as _detect_course_conflicts

# edu-config 会创建的静态 tools
try:
    from app.agent.tools.edu_guide_tool import query_edu_guide as _query_edu_guide
except ImportError:
    _query_edu_guide = None

try:
    from app.agent.tools.notification_tools import query_notifications as _query_notifications
except ImportError:
    _query_notifications = None


def create_tools(
    db: AsyncSession,
    user_id: str,
    student_no: str = "",
    rag_manager=None,
    upload_dir: Optional[str] = None,
) -> list:
    """
    创建并返回所有 Agent Tool 的列表。

    Args:
        db: 异步数据库会话
        user_id: 当前用户 UUID
        student_no: 当前用户的学号
        rag_manager: RAGManager 实例（可选，兼容旧调用方，优先使用）
        upload_dir: 文件上传目录（可选，传给 create_knowledge_tools）

    Returns:
        LangChain BaseTool 列表
    """
    # ═══ 核心 Tool 定义 ═══

    # Tool 元数据: (name, func, description)
    tool_defs = [
        # ── 课表 ──
        (
            "query_courses",
            _query_courses,
            "查询学生课表。参数: week_day(1-7可选), course_name(可选,模糊)。"
            "无参数默认返回当前学期本周课表。"
            "触发: 「周一有什么课」「高数在哪个教室」「这周课表」等。",
        ),
        # ── 成绩 ──
        (
            "query_scores",
            _query_scores,
            "查询学生成绩。参数: term(如2025-2026-1,可选), course_name(可选,模糊)。"
            "无参数返回全部成绩。"
            "触发: 「上学期成绩」「高数考了多少」「成绩」等。",
        ),
        # ── 考试 ──
        (
            "query_exams",
            _query_exams,
            "查询考试安排。无参数返回当前学期考试。参数: course_name(可选)。"
            "触发: 「什么时候考试」「期末」「考试」等。",
        ),
        # ── 学生信息 ──
        (
            "query_student_info",
            _query_student_info,
            "查询学生基本信息(姓名/学院/专业/班级/年级/校区)。无参数。"
            "触发: 「我的信息」「我是哪个专业」「我的学院」等。",
        ),
        (
            "query_academic_status",
            _query_academic_status,
            "查询学业进度(GPA/学分/各模块完成度)。无参数。"
            "触发: 「还差多少学分」「绩点多少」「学业进度」等。",
        ),
        (
            "query_warnings",
            _query_warnings,
            "查询学籍预警和警告信息。无参数。"
            "触发: 「挂科」「预警」「警告」等。",
        ),
        # ── 培养方案/选课/教室 ──
        (
            "query_training_plan",
            _query_training_plan,
            "查询培养方案。参数: course_type(可选,'必修'/'选修')。"
            "触发: 「培养方案」「要修哪些课」「必修课」等。",
        ),
        (
            "query_selected_courses",
            _query_selected_courses,
            "查询已选课程列表。无参数。"
            "触发: 「选了哪些课」「选课结果」等。",
        ),
        (
            "query_classrooms",
            _query_classrooms,
            "查询空闲教室。参数: week_day(可选,1-7), building(可选,教学楼名)。"
            "触发: 「空教室」「哪有教室」等。",
        ),
        # ── 学业规划 ──
        (
            "analyze_credit_gap",
            _analyze_credit_gap,
            "分析学分缺口：按模块组对比已修学分 vs 要求学分。无参数。"
            "触发: 「学分缺口」「还差多少学分」「毕业还差什么」「模块进度」等。",
        ),
        (
            "check_required_courses",
            _check_required_courses,
            "检查必修课完成情况：列出未修/未通过的必修课。无参数。"
            "触发: 「必修课」「还有哪些必修」「必修修完了吗」等。",
        ),
        (
            "recommend_courses",
            _recommend_courses,
            "基于学分缺口推荐选课。参数: target_semester(可选), max_count(可选,默认10)。"
            "触发: 「选课推荐」「下学期选什么」「推荐选课」等。",
        ),
        (
            "plan_academic_path",
            _plan_academic_path,
            "规划剩余学期学业路径。参数: credits_per_semester(可选,默认25)。"
            "触发: 「学业规划」「怎么安排选课」「毕业规划」「还剩几学期」等。",
        ),
        # ── P6: GPA 模拟器 + 冲突检测 ──
        (
            "simulate_gpa",
            _simulate_gpa,
            "模拟 GPA 计算：输入预估课程(JSON数组)，输出模拟后GPA及变化。"
            "参数: courses_json (JSON字符串, 格式 [{\"name\":\"课程名\",\"credit\":3.0,\"score\":90}, ...], 最多10门)。"
            "触发: 「如果我高数考90分GPA多少」「模拟GPA」「绩点计算」「GPA计算器」等。",
        ),
        (
            "detect_course_conflicts",
            _detect_course_conflicts,
            "检测课表课程时间冲突（同一天时段重叠+周次重叠）。无参数，自动检测全部课程。"
            "触发: 「课表冲突」「有没有撞课」「时间冲突」「课程重叠」「冲突检测」等。",
        ),
    ]

    tools = []
    for name, func, description in tool_defs:
        # 对需要 student_no 的 Tool 额外绑定 student_no
        if name in (
            "analyze_credit_gap", "check_required_courses",
            "recommend_courses", "plan_academic_path",
        ):
            async def _bound(fn=func, db=db, uid=user_id, sno=student_no, **kwargs):
                return await fn(db, uid, sno, **kwargs)
        else:
            async def _bound(fn=func, db=db, uid=user_id, **kwargs):
                return await fn(db, uid, **kwargs)

        # 给闭包函数一个明确的名称（方便调试）
        _bound.__name__ = f"{name}_bound"

        t = StructuredTool.from_function(
            name=name,
            description=description,
            coroutine=_bound,
            infer_schema=False,  # 闭包无类型标注，依赖 description 指导 LLM
        )
        tools.append(t)

    # ── 知识库 Tools (工厂模式) ──
    knowledge_tools = create_knowledge_tools(
        user_id=user_id,
        db_session=db,
        upload_dir=upload_dir,
    )
    tools.extend(knowledge_tools)

    # ── 静态 Tool: edu_guide (无 db 依赖) ──
    if _query_edu_guide is not None:
        t = StructuredTool.from_function(
            name="query_edu_guide",
            description=(
                "搜索教务系统功能使用指南。参数: query(搜索关键词或问题)。"
                "触发: 「怎么查课表」「缓考怎么办理」「转专业怎么办」等。"
            ),
            coroutine=_query_edu_guide,
        )
        tools.append(t)

    # ── 静态 Tool: notifications ──
    if _query_notifications is not None:
        async def _notif_bound(db=db, uid=user_id, **kwargs):
            return await _query_notifications(db, uid, **kwargs)
        _notif_bound.__name__ = "query_notifications_bound"

        t = StructuredTool.from_function(
            name="query_notifications",
            description=(
                "搜索教务通知/文件/消息。参数: category(可选,'通知'/'文件'/'消息'), "
                "keyword(可选,模糊搜索), limit(可选,默认20)。"
                "触发: 「最近有什么通知」「选课通知」「教务处的文件」等。"
            ),
            coroutine=_notif_bound,
            infer_schema=False,
        )
        tools.append(t)

    return tools
