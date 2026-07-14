# models.py — SQLAlchemy ORM 模型 (16表)
# 3张新增表 + 13张教务表（全部添加 user_id 实现多用户隔离）
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, Text, Boolean, DateTime,
    ForeignKey, Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.session import Base


def new_uuid() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ═══════════════════════════════════════════════════
# 新增表 (3张) — 多用户核心
# ═══════════════════════════════════════════════════

class User(Base):
    """用户表 — 应用层认证"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True)
    phone = Column(String(20), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # 关系
    edu_credential = relationship("EduCredential", back_populates="user", uselist=False)
    sync_logs = relationship("SyncLog", back_populates="user")

    def __repr__(self):
        return f"<User {self.username}>"


class EduCredential(Base):
    """教务凭证表 — AES-256-GCM 加密存储"""
    __tablename__ = "edu_credentials"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"),
        unique=True, nullable=False, index=True
    )
    student_no = Column(String(30), nullable=False)
    login_account = Column(String(100), nullable=False)
    encrypted_password = Column(Text, nullable=False)  # AES-256-GCM (Fernet)
    base_url = Column(String(255), default="https://jwglxt.buct.edu.cn")
    doubao_api_key = Column(Text, nullable=True)  # 用户自备豆包Key (加密)
    doubao_model = Column(String(100), nullable=True)
    last_sync_at = Column(DateTime, nullable=True)
    is_valid = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="edu_credential")

    def __repr__(self):
        return f"<EduCredential user={self.user_id} student={self.student_no}>"


class SyncLog(Base):
    """同步日志表 — 记录每次数据同步"""
    __tablename__ = "sync_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    module = Column(String(50), nullable=False)
    status = Column(String(20), default="running")  # running/success/failed
    record_count = Column(Integer, default=0)
    error_msg = Column(Text, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    started_at = Column(DateTime, default=utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="sync_logs")

    __table_args__ = (
        Index("idx_synclog_user_module", "user_id", "module", "started_at"),
    )

    def __repr__(self):
        return f"<SyncLog {self.module} {self.status}>"


# ═══════════════════════════════════════════════════
# 教务数据表 (13张) — 全部添加 user_id + 索引
# ═══════════════════════════════════════════════════

class Student(Base):
    """学生基本信息"""
    __tablename__ = "edu_student"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    student_no = Column(String(30), nullable=False, index=True)
    name = Column(String(50), nullable=True)
    gender = Column(String(10), nullable=True)
    college = Column(String(100), nullable=True)
    major = Column(String(100), nullable=True)
    class_name = Column(String(100), nullable=True)
    grade = Column(String(10), nullable=True)
    campus = Column(String(50), nullable=True)
    edu_level = Column(String(20), nullable=True)
    raw_data = Column(Text, nullable=True)
    sync_time = Column(DateTime, default=utcnow)

    __table_args__ = (
        Index("idx_student_user", "user_id", "student_no"),
    )


class Course(Base):
    """课程表（本学期课表）"""
    __tablename__ = "edu_course"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    student_no = Column(String(30), nullable=False)
    course_code = Column(String(50), default="")
    course_name = Column(String(200), nullable=False)
    teacher = Column(String(100), default="")
    teacher_title = Column(String(50), default="")
    classroom = Column(String(100), default="")
    campus = Column(String(50), default="")
    building = Column(String(50), default="")
    week_day = Column(Integer, nullable=True)
    start_node = Column(Integer, nullable=True)
    end_node = Column(Integer, nullable=True)
    start_week = Column(Integer, nullable=True)
    end_week = Column(Integer, nullable=True)
    week_info = Column(String(100), default="")
    credit = Column(Float, default=0.0)
    course_type = Column(String(50), default="")
    sync_hash = Column(String(64), default="")
    sync_time = Column(DateTime, default=utcnow)

    __table_args__ = (
        Index("idx_course_user_wd", "user_id", "week_day"),
        Index("idx_course_user_code", "user_id", "course_code"),
    )


class Score(Base):
    """成绩表（汇总）"""
    __tablename__ = "edu_score"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    student_no = Column(String(30), nullable=False)
    term = Column(String(20), default="")
    course_name = Column(String(200), nullable=False)
    course_code = Column(String(50), default="")
    score = Column(String(20), default="")
    credit = Column(Float, default=0.0)
    grade_point = Column(Float, default=0.0)
    course_type = Column(String(50), default="")
    exam_type = Column(String(50), default="")
    sync_hash = Column(String(64), default="")
    sync_time = Column(DateTime, default=utcnow)

    __table_args__ = (
        Index("idx_score_user_term", "user_id", "term"),
        Index("idx_score_user_course", "user_id", "course_name"),
    )


class ScoreDetail(Base):
    """成绩明细表"""
    __tablename__ = "edu_score_detail"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    student_no = Column(String(30), nullable=False)
    course_name = Column(String(200), default="")
    course_code = Column(String(50), default="")
    credit = Column(Float, default=0.0)
    score = Column(String(20), default="")
    grade_point = Column(Float, default=0.0)
    course_type = Column(String(50), default="")
    exam_type = Column(String(50), default="")
    term = Column(String(20), default="")
    sync_time = Column(DateTime, default=utcnow)

    __table_args__ = (
        Index("idx_scoredetail_user_term", "user_id", "term"),
    )


class Exam(Base):
    """考试安排"""
    __tablename__ = "edu_exam"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    student_no = Column(String(30), nullable=False)
    course_name = Column(String(200), default="")
    exam_date = Column(String(20), default="")
    exam_time = Column(String(30), default="")
    classroom = Column(String(100), default="")
    seat_no = Column(String(20), default="")
    exam_type = Column(String(50), default="")
    campus = Column(String(50), default="")
    sync_time = Column(DateTime, default=utcnow)

    __table_args__ = (
        Index("idx_exam_user_date", "user_id", "exam_date"),
    )


class AcademicWarning(Base):
    """学业预警"""
    __tablename__ = "edu_academic_warning"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    student_no = Column(String(30), nullable=False)
    warning_type = Column(String(50), default="")
    warning_level = Column(String(20), default="")
    description = Column(Text, default="")
    create_time = Column(String(30), default="")
    status = Column(String(20), default="")
    sync_time = Column(DateTime, default=utcnow)


class AcademicStatus(Base):
    """学业状态（学分统计）"""
    __tablename__ = "edu_academic_status"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    student_no = Column(String(30), nullable=False)
    total_credits = Column(Float, default=0.0)
    earned_credits = Column(Float, default=0.0)
    failed_credits = Column(Float, default=0.0)
    gpa_sum = Column(Float, default=0.0)
    average_gpa = Column(Float, default=0.0)
    required_done = Column(Integer, default=0)
    required_total = Column(Integer, default=0)
    elective_done = Column(Integer, default=0)
    elective_total = Column(Integer, default=0)
    raw_data = Column(Text, default="")
    sync_time = Column(DateTime, default=utcnow)


class GraduationAudit(Base):
    """毕业审核"""
    __tablename__ = "edu_graduation_audit"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    student_no = Column(String(30), nullable=False)
    check_item = Column(String(200), default="")
    requirement = Column(Text, default="")
    status = Column(String(50), default="")
    detail = Column(Text, default="")
    sync_time = Column(DateTime, default=utcnow)


class Classroom(Base):
    """空闲教室"""
    __tablename__ = "edu_classroom"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    campus = Column(String(50), default="")
    building = Column(String(50), default="")
    room_no = Column(String(50), default="")
    capacity = Column(Integer, default=0)
    week_day = Column(Integer, default=0)
    start_node = Column(Integer, default=0)
    end_node = Column(Integer, default=0)
    week_range = Column(String(50), default="")
    status = Column(String(20), default="")
    sync_time = Column(DateTime, default=utcnow)


class TrainingPlan(Base):
    """培养方案"""
    __tablename__ = "edu_training_plan"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    major = Column(String(100), default="")
    grade = Column(String(10), default="")
    course_code = Column(String(50), default="")
    course_name = Column(String(200), default="")
    credit = Column(Float, default=0.0)
    course_type = Column(String(50), default="")
    module_group = Column(String(100), default="")
    semester = Column(String(20), default="")
    is_required = Column(Integer, default=0)
    sync_time = Column(DateTime, default=utcnow)

    __table_args__ = (
        Index("idx_training_major", "user_id", "major", "grade"),
    )


class SelectedCourse(Base):
    """已选课程"""
    __tablename__ = "edu_selected_course"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    student_no = Column(String(30), nullable=False)
    course_code = Column(String(50), default="")
    course_name = Column(String(200), default="")
    teacher = Column(String(100), default="")
    credit = Column(Float, default=0.0)
    course_type = Column(String(50), default="")
    classroom = Column(String(100), default="")
    week_day = Column(Integer, default=0)
    start_node = Column(Integer, default=0)
    end_node = Column(Integer, default=0)
    week_range = Column(String(50), default="")
    select_type = Column(String(50), default="")
    sync_time = Column(DateTime, default=utcnow)


class Notification(Base):
    """教务通知"""
    __tablename__ = "edu_notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    category = Column(String(50), default="")
    tag = Column(String(50), default="")
    title = Column(String(500), default="")
    content = Column(Text, default="")
    date = Column(String(30), default="")
    link = Column(String(500), default="")
    sync_time = Column(DateTime, default=utcnow)


class AgentSession(Base):
    """Agent 对话会话记录"""
    __tablename__ = "agent_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    session_key = Column(String(64), unique=True, nullable=False, index=True)
    title = Column(String(200), default="新对话")
    last_message_preview = Column(String(100), nullable=True)
    message_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    messages = relationship("AgentMessage", back_populates="session", cascade="all, delete-orphan")


class AgentMessage(Base):
    """Agent 对话消息记录 — 支持多设备同步和断线重连"""
    __tablename__ = "agent_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(
        Integer, ForeignKey("agent_sessions.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    role = Column(String(20), nullable=False)  # user / assistant / tool
    content = Column(Text, nullable=True)
    tool_name = Column(String(100), nullable=True)  # role=tool 时的工具名
    event_id = Column(Integer, nullable=True)  # SSE 事件序号，断线重连用
    created_at = Column(DateTime, default=utcnow, nullable=False)

    session = relationship("AgentSession", back_populates="messages")

    __table_args__ = (
        Index("idx_msg_session_event", "session_id", "event_id"),
    )
