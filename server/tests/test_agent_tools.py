# tests/test_agent_tools.py — Agent Tool 单元测试
"""测试 Tool 工厂和核心 Tool 逻辑（mock Repository，无需数据库）"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.unit
class TestToolFactory:
    """测试 create_tools() 工厂函数"""

    def test_create_tools_returns_all(self):
        """工厂返回正确数量的工具（14核心 + N知识库）"""
        from app.agent.tools import create_tools

        mock_db = MagicMock()
        tools = create_tools(db=mock_db, user_id="test-user-1", student_no="2024050020")

        assert len(tools) >= 14, f"期望 >=14 个 Tool，实际 {len(tools)}"
        tool_names = [t.name for t in tools]
        assert "query_courses" in tool_names
        assert "query_scores" in tool_names
        assert "query_exams" in tool_names
        assert "query_student_info" in tool_names
        assert "analyze_credit_gap" in tool_names
        assert "check_required_courses" in tool_names
        assert "plan_academic_path" in tool_names

    def test_tools_have_correct_attributes(self):
        """每个 Tool 有 name 和 description"""
        from app.agent.tools import create_tools

        mock_db = MagicMock()
        tools = create_tools(db=mock_db, user_id="u1", student_no="s1")

        for t in tools:
            assert t.name, f"Tool 缺少 name"
            assert t.description, f"Tool {t.name} 缺少 description"
            assert callable(t), f"Tool {t.name} 不可调用"

    def test_core_tools_are_callable(self):
        """核心工具可以被调用（会被 mock DB 阻止但不会产生导入错误）"""
        from app.agent.tools import create_tools

        mock_db = MagicMock()
        tools = create_tools(db=mock_db, user_id="u1")

        core = [t for t in tools if t.name in (
            "query_courses", "query_scores", "query_exams",
        )]
        assert len(core) == 3
        for t in core:
            # 验证工具是一个可调用对象
            assert hasattr(t, 'func') or hasattr(t, 'coroutine') or callable(t)


@pytest.mark.unit
class TestCourseQuery:
    """测试课表查询逻辑（mock Repository）"""

    @pytest.fixture
    def mock_courses(self):
        """模拟课表数据"""
        return [
            MagicMock(
                week_day=1, start_node=1, end_node=2,
                course_name="高等数学A",
                teacher="张教授", classroom="教学楼101",
                course_type="必修", credit="4",
                start_week=1, end_week=16,
            ),
            MagicMock(
                week_day=3, start_node=3, end_node=4,
                course_name="线性代数",
                teacher="李教授", classroom="教学楼202",
                course_type="必修", credit="2",
                start_week=1, end_week=16,
            ),
        ]

    @pytest.mark.asyncio
    async def test_query_courses_all(self, mock_courses):
        """查询全部课表"""
        from app.agent.tools.course_tools import query_courses

        mock_db = AsyncMock()
        mock_repo = MagicMock()
        mock_repo.get_all = AsyncMock(return_value=mock_courses)

        with patch("app.agent.tools.course_tools.CourseRepo", return_value=mock_repo):
            with patch("app.agent.tools.course_tools.get_current_semester", return_value={
                "term_name": "2025-2026-2", "week": 8,
            }):
                result = await query_courses(mock_db, "user-1")

        assert "课表" in result
        assert "高等数学A" in result
        assert "线性代数" in result

    @pytest.mark.asyncio
    async def test_query_courses_empty(self):
        """无课表数据时的提示"""
        from app.agent.tools.course_tools import query_courses

        mock_db = AsyncMock()
        mock_repo = MagicMock()
        mock_repo.get_all = AsyncMock(return_value=[])

        with patch("app.agent.tools.course_tools.CourseRepo", return_value=mock_repo):
            with patch("app.agent.tools.course_tools.get_current_semester", return_value={
                "term_name": "2025-2026-2", "week": 8,
            }):
                result = await query_courses(mock_db, "user-1")

        assert "没有课表数据" in result or "无课" in result

    @pytest.mark.asyncio
    async def test_query_courses_by_weekday(self, mock_courses):
        """按周几筛选"""
        from app.agent.tools.course_tools import query_courses

        mock_db = AsyncMock()
        mock_repo = MagicMock()
        mock_repo.get_by_weekday = AsyncMock(return_value=[mock_courses[0]])

        with patch("app.agent.tools.course_tools.CourseRepo", return_value=mock_repo):
            with patch("app.agent.tools.course_tools.get_current_semester", return_value={
                "term_name": "2025-2026-2", "week": 8,
            }):
                result = await query_courses(mock_db, "user-1", week_day=1)

        assert "高等数学A" in result
        assert "周一" in result or "1" in result


@pytest.mark.unit
class TestScoreQuery:
    """测试成绩查询逻辑"""

    @pytest.mark.asyncio
    async def test_query_scores_empty(self):
        """无成绩数据时的提示"""
        from app.agent.tools.score_tools import query_scores

        mock_db = AsyncMock()
        mock_repo = MagicMock()
        mock_repo.get_all = AsyncMock(return_value=[])

        with patch("app.agent.tools.score_tools.ScoreRepo", return_value=mock_repo):
            result = await query_scores(mock_db, "user-1")

        assert "成绩" in result
        assert "没有" in result or "无" in result

    @pytest.mark.asyncio
    async def test_query_scores_all(self):
        """有成绩数据"""
        from app.agent.tools.score_tools import query_scores

        mock_db = AsyncMock()
        mock_repo = MagicMock()
        mock_score = MagicMock(
            course_name="高等数学A", score="85.0", term="2025-2026-1",
            credit="4.0", grade_point="3.7", course_type="必修",
        )
        mock_repo.get_all = AsyncMock(return_value=[mock_score])

        with patch("app.agent.tools.score_tools.ScoreRepo", return_value=mock_repo):
            result = await query_scores(mock_db, "user-1")

        assert "高等数学A" in result


@pytest.mark.unit
class TestStudentInfo:
    """测试学生信息查询"""

    @pytest.mark.asyncio
    async def test_query_student_info_found(self):
        """查到学生信息"""
        from app.agent.tools.student_tools import query_student_info

        mock_db = AsyncMock()
        mock_student = MagicMock()
        mock_student.name = "张三"
        mock_student.student_no = "2024050020"
        mock_student.gender = "男"
        mock_student.college = "信息科学与技术学院"
        mock_student.major = "计算机科学与技术"
        mock_student.class_name = "计科2001"
        mock_student.grade = "2024"
        mock_student.campus = "北校区"
        mock_student.edu_level = "本科"

        mock_repo = MagicMock()
        mock_repo.get_one = AsyncMock(return_value=mock_student)

        with patch("app.agent.tools.student_tools.StudentRepo", return_value=mock_repo):
            result = await query_student_info(mock_db, "user-1")

        assert "张三" in result
        assert "计算机科学与技术" in result
        assert "北校区" in result
