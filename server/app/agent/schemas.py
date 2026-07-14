# schemas.py — Agent Pydantic 请求/响应 + SSE 事件模型 (P3)
from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════
# 请求
# ═══════════════════════════════════════════════════

class ChatRequest(BaseModel):
    """SSE 聊天请求"""
    message: str = Field(..., min_length=1, max_length=4000, description="用户消息")
    session_key: Optional[str] = Field(None, max_length=64, description="已有会话key，不传则新建")


# ═══════════════════════════════════════════════════
# 响应
# ═══════════════════════════════════════════════════

class AgentSessionResponse(BaseModel):
    """会话列表项"""
    session_key: str
    title: str
    last_message_preview: Optional[str] = None
    message_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AgentSessionListResponse(BaseModel):
    """会话列表"""
    sessions: list[AgentSessionResponse]
    total: int


class AgentMessageResponse(BaseModel):
    """消息历史项"""
    role: str
    content: Optional[str] = None
    tool_name: Optional[str] = None
    event_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AgentMessageListResponse(BaseModel):
    """消息历史"""
    messages: list[AgentMessageResponse]
    has_more: bool


class AgentDeleteResponse(BaseModel):
    """删除结果"""
    ok: bool = True
    session_key: str


# ═══════════════════════════════════════════════════
# SSE 事件模型
# ═══════════════════════════════════════════════════

class SSEEvent:
    """SSE 事件 — 序列化为 text/event-stream 行"""

    HEARTBEAT_INTERVAL = 30  # 心跳间隔（秒）

    def __init__(
        self,
        event_type: str,
        data: dict = None,
        event_id: int = None,
    ):
        """
        event_type: meta | token | tool_start | tool_end | done | error | heartbeat
        """
        self.type = event_type
        self.data = data or {}
        self.id = event_id

    def to_sse(self) -> str:
        """转为 SSE 文本格式"""
        lines: list[str] = []
        if self.id is not None:
            lines.append(f"id: {self.id}")
        lines.append(f"event: {self.type}")
        import json
        lines.append(f"data: {json.dumps(self.data, ensure_ascii=False)}")
        lines.append("")  # 空行分隔
        return "\n".join(lines)

    @classmethod
    def meta(cls, session_key: str, event_id: int = 0) -> "SSEEvent":
        return cls("meta", {"type": "meta", "session_key": session_key}, event_id)

    @classmethod
    def token(cls, content: str, event_id: int) -> "SSEEvent":
        return cls("token", {"type": "token", "content": content}, event_id)

    @classmethod
    def tool_start(cls, tool_name: str, event_id: int) -> "SSEEvent":
        return cls("tool_start", {"type": "tool_start", "tool": tool_name}, event_id)

    @classmethod
    def tool_end(cls, tool_name: str, event_id: int) -> "SSEEvent":
        return cls("tool_end", {"type": "tool_end", "tool": tool_name}, event_id)

    @classmethod
    def done(cls, session_key: str, message_id: int, event_id: int) -> "SSEEvent":
        return cls("done", {
            "type": "done",
            "session_key": session_key,
            "message_id": message_id,
        }, event_id)

    @classmethod
    def error(cls, message: str, event_id: int = None) -> "SSEEvent":
        return cls("error", {"type": "error", "message": message}, event_id)

    @classmethod
    def heartbeat(cls) -> str:
        """心跳注释行 — 客户端忽略"""
        return ": heartbeat\n\n"
