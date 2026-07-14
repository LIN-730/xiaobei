# repos.py — 各表 Repository 实现
# 每个 Repo 继承 BaseRepository，设置对应 model
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.base import BaseRepository
from app.database.models import (
    Student, Course, Score, ScoreDetail, Exam,
    AcademicWarning, AcademicStatus, GraduationAudit,
    Classroom, TrainingPlan, SelectedCourse, Notification,
    SyncLog, AgentSession, AgentMessage,
)


class StudentRepo(BaseRepository):
    model = Student


class CourseRepo(BaseRepository):
    model = Course

    async def get_by_weekday(self, week_day: int):
        """按星期获取课表"""
        from sqlalchemy import select
        stmt = (
            select(self.model)
            .where(self.model.user_id == self.user_id)
            .where(self.model.week_day == week_day)
            .order_by(self.model.start_node)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


class ScoreRepo(BaseRepository):
    model = Score

    async def get_by_term(self, term: str):
        """按学期获取成绩"""
        from sqlalchemy import select
        stmt = (
            select(self.model)
            .where(self.model.user_id == self.user_id)
            .where(self.model.term == term)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_all_terms(self) -> list:
        """获取所有学期列表"""
        from sqlalchemy import select, distinct
        stmt = (
            select(distinct(self.model.term))
            .where(self.model.user_id == self.user_id)
            .order_by(self.model.term)
        )
        result = await self.db.execute(stmt)
        return [row[0] for row in result.all() if row[0]]

    async def get_gpa_stats(self):
        """GPA 统计"""
        from sqlalchemy import select, func
        stmt = (
            select(
                func.count(self.model.id),
                func.sum(self.model.credit),
                func.avg(self.model.grade_point),
            )
            .where(self.model.user_id == self.user_id)
            .where(self.model.grade_point > 0)
        )
        result = await self.db.execute(stmt)
        row = result.one()
        return {
            "course_count": row[0] or 0,
            "total_credits": row[1] or 0.0,
            "avg_gpa": round(row[2] or 0.0, 2),
        }


class ScoreDetailRepo(BaseRepository):
    model = ScoreDetail


class ExamRepo(BaseRepository):
    model = Exam

    async def get_upcoming(self, limit: int = 10):
        """获取即将到来的考试"""
        records = await self.get_all()
        records.sort(key=lambda e: e.exam_date or "")
        return records[:limit]


class AcademicWarningRepo(BaseRepository):
    model = AcademicWarning


class AcademicStatusRepo(BaseRepository):
    model = AcademicStatus

    async def get_status(self):
        """获取学业状态（取最新一条）"""
        return await self.get_one()


class GraduationAuditRepo(BaseRepository):
    model = GraduationAudit


class ClassroomRepo(BaseRepository):
    model = Classroom

    async def get_by_weekday(self, week_day: int, building: str = None):
        """按星期和教学楼筛选空闲教室"""
        from sqlalchemy import select
        stmt = (
            select(self.model)
            .where(self.model.user_id == self.user_id)
            .where(self.model.week_day == week_day)
        )
        if building:
            stmt = stmt.where(self.model.building == building)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


class TrainingPlanRepo(BaseRepository):
    model = TrainingPlan

    async def get_by_type(self, course_type: str = None):
        """按类型筛选培养方案"""
        from sqlalchemy import select
        stmt = select(self.model).where(self.model.user_id == self.user_id)
        if course_type:
            stmt = stmt.where(self.model.course_type == course_type)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


class SelectedCourseRepo(BaseRepository):
    model = SelectedCourse


class NotificationRepo(BaseRepository):
    model = Notification


class SyncLogRepo(BaseRepository):
    model = SyncLog

    async def get_latest(self, module: str = None):
        """获取最近同步日志"""
        from sqlalchemy import select
        stmt = (
            select(self.model)
            .where(self.model.user_id == self.user_id)
            .order_by(self.model.started_at.desc())
            .limit(1)
        )
        if module:
            stmt = stmt.where(self.model.module == module)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def log_start(self, module: str):
        """记录同步开始"""
        log = SyncLog(user_id=self.user_id, module=module, status="running")
        self.db.add(log)
        await self.db.commit()
        return log

    async def log_complete(self, module: str, record_count: int, duration_ms: int):
        """记录同步完成"""
        log = await self.get_latest(module=module)
        if log and log.status == "running":
            log.status = "success"
            log.record_count = record_count
            log.duration_ms = duration_ms
            log.completed_at = datetime.now(timezone.utc)
            await self.db.commit()

    async def log_fail(self, module: str, error: str):
        """记录同步失败"""
        log = await self.get_latest(module=module)
        if log and log.status == "running":
            log.status = "failed"
            log.error_msg = error
            log.completed_at = datetime.now(timezone.utc)
            await self.db.commit()


# ═══════════════════════════════════════════════════
# Agent Repository (P3)
# ═══════════════════════════════════════════════════

class AgentSessionRepo:
    """Agent 会话 Repository — 管理对话会话"""

    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id

    async def create(self, session_key: str, title: str = "新对话") -> AgentSession:
        """创建新会话"""
        session = AgentSession(
            user_id=self.user_id,
            session_key=session_key,
            title=title,
            message_count=0,
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get_by_key(self, session_key: str) -> Optional[AgentSession]:
        """按 session_key 获取会话"""
        stmt = (
            select(AgentSession)
            .where(AgentSession.user_id == self.user_id)
            .where(AgentSession.session_key == session_key)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, session_id: int) -> Optional[AgentSession]:
        """按 ID 获取会话"""
        stmt = (
            select(AgentSession)
            .where(AgentSession.user_id == self.user_id)
            .where(AgentSession.id == session_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_sessions(self, limit: int = 50, offset: int = 0) -> list[AgentSession]:
        """获取用户的会话列表（按更新时间倒序）"""
        stmt = (
            select(AgentSession)
            .where(AgentSession.user_id == self.user_id)
            .order_by(AgentSession.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_title(self, session_key: str, title: str) -> bool:
        """更新会话标题"""
        session = await self.get_by_key(session_key)
        if session:
            session.title = title
            await self.db.commit()
            return True
        return False

    async def increment_message_count(self, session_id: int) -> None:
        """增加消息计数"""
        session = await self.get_by_id(session_id)
        if session:
            session.message_count = (session.message_count or 0) + 1
            await self.db.commit()

    async def update_preview(self, session_id: int, preview: str) -> None:
        """更新最后一条消息预览（前50字）"""
        session = await self.get_by_id(session_id)
        if session:
            session.last_message_preview = preview[:100] if preview else None
            await self.db.commit()

    async def delete(self, session_key: str) -> bool:
        """删除会话及其所有消息（cascade）"""
        session = await self.get_by_key(session_key)
        if session:
            await self.db.delete(session)
            await self.db.commit()
            return True
        return False


class AgentMessageRepo:
    """Agent 消息 Repository — 持久化对话消息，支持分页和断线重连"""

    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id

    async def add(
        self,
        session_id: int,
        role: str,
        content: str = None,
        tool_name: str = None,
        event_id: int = None,
    ) -> AgentMessage:
        """添加一条消息"""
        msg = AgentMessage(
            session_id=session_id,
            role=role,
            content=content,
            tool_name=tool_name,
            event_id=event_id,
        )
        self.db.add(msg)
        await self.db.commit()
        await self.db.refresh(msg)
        return msg

    async def list_by_session(
        self,
        session_id: int,
        before_id: int = None,
        limit: int = 50,
    ) -> list[AgentMessage]:
        """按会话获取消息（分页：before_id 之前的消息）"""
        stmt = (
            select(AgentMessage)
            .where(AgentMessage.session_id == session_id)
            .order_by(AgentMessage.event_id.desc())
            .limit(limit)
        )
        if before_id is not None:
            stmt = stmt.where(AgentMessage.event_id < before_id)
        result = await self.db.execute(stmt)
        messages = list(result.scalars().all())
        messages.reverse()  # 返回时间正序
        return messages

    async def get_last_event_id(self, session_id: int) -> int:
        """获取该会话最后一条消息的 event_id（用于断线重连）"""
        from sqlalchemy import func as _func
        stmt = (
            select(_func.max(AgentMessage.event_id))
            .where(AgentMessage.session_id == session_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def count_by_session(self, session_id: int) -> int:
        """统计会话消息数"""
        stmt = (
            select(func.count())
            .select_from(AgentMessage)
            .where(AgentMessage.session_id == session_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0
