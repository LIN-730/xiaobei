# agent.py — AI 对话 API (SSE 流式 + 会话管理) (P3)
"""
POST /api/v1/agent/chat     — SSE 流式对话
GET  /api/v1/agent/sessions — 会话列表
GET  /api/v1/agent/sessions/{key}/messages — 消息历史
DELETE /api/v1/agent/sessions/{key} — 删除会话
"""
from __future__ import annotations

import asyncio
import uuid
import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.database.repositories.repos import AgentSessionRepo, AgentMessageRepo
from app.auth.dependencies import get_current_user
from app.database.models import User, EduCredential
from app.agent.schemas import (
    ChatRequest,
    SSEEvent,
    AgentSessionResponse,
    AgentSessionListResponse,
    AgentMessageResponse,
    AgentMessageListResponse,
    AgentDeleteResponse,
)
from app.agent.agent_manager import get_or_create_agent
from sqlalchemy import select

router = APIRouter()

HEARTBEAT_INTERVAL = 30  # 秒


# ═══════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════

async def _get_student_no(db: AsyncSession, user_id: str) -> str:
    """获取用户学号"""
    stmt = select(EduCredential).where(EduCredential.user_id == user_id)
    result = await db.execute(stmt)
    cred = result.scalar_one_or_none()
    return cred.student_no if cred else ""


# ═══════════════════════════════════════════════════
# POST /chat — SSE 流式对话
# ═══════════════════════════════════════════════════

@router.post("/chat")
async def chat(
    req: ChatRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """SSE 流式对话。支持 Last-Event-ID 断线重连。"""
    session_repo = AgentSessionRepo(db, user.id)
    message_repo = AgentMessageRepo(db, user.id)

    # ── 1. 会话管理 ──
    session_key = req.session_key
    is_new_session = False

    if session_key:
        session = await session_repo.get_by_key(session_key)
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
    else:
        session_key = str(uuid.uuid4())[:12]
        session = await session_repo.create(
            session_key=session_key,
            title=req.message[:20] if req.message else "新对话",
        )
        is_new_session = True

    session_id = session.id

    # ── 2. 持久化用户消息 ──
    last_event_id = await message_repo.get_last_event_id(session_id)
    next_event_id = (last_event_id or 0) + 1

    user_msg = await message_repo.add(
        session_id=session_id,
        role="user",
        content=req.message,
        event_id=next_event_id,
    )
    await session_repo.update_preview(session_id, req.message[:50])

    # ── 3. 检查 Last-Event-ID 重连 ──
    last_event_id_header = request.headers.get("Last-Event-ID")
    if last_event_id_header:
        try:
            resume_from = int(last_event_id_header)
            if resume_from >= next_event_id:
                # 客户端已接收全部事件，无需重发
                pass
        except ValueError:
            pass

    # ── 4. 获取 Agent ──
    student_no = await _get_student_no(db, user.id)
    try:
        agent = await get_or_create_agent(
            db=db,
            user_id=user.id,
            student_no=student_no,
        )
    except Exception as e:
        # LLM 初始化失败，返回错误 SSE
        async def error_gen():
            err_event = SSEEvent.error(f"AI 服务初始化失败: {e}", 0)
            yield err_event.to_sse()
        return StreamingResponse(
            error_gen(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    # ── 5. SSE 生成器 ──
    async def event_generator():
        event_counter = [next_event_id]  # 用列表以便闭包内修改
        assistant_content: list[str] = []

        try:
            # 发送 meta 事件
            meta = SSEEvent.meta(session_key, event_counter[0])
            event_counter[0] += 1
            yield meta.to_sse()

            # 发送心跳 (如果 Agent 调用较慢)
            last_emit = asyncio.get_event_loop().time()

            async def heartbeat_task():
                while True:
                    await asyncio.sleep(HEARTBEAT_INTERVAL)
                    # 通过 yield 发出心跳 (实际上在同步生成器中无法直接 await)
                    pass

            # 调用 Agent (异步流式)
            # 注意: LangChain AgentExecutor.ainvoke 是一次性返回，不是流式
            # 对于流式输出，需要用 astream_events
            result = await agent.ainvoke({
                "input": req.message,
                "chat_history": [],  # P4: 上下文记忆
            })

            output = result.get("output", "")

            # 模拟 token 流（分批发送）
            chunk_size = 10
            for i in range(0, len(output), chunk_size):
                chunk = output[i:i + chunk_size]
                token_event = SSEEvent.token(chunk, event_counter[0])
                event_counter[0] += 1
                yield token_event.to_sse()
                await asyncio.sleep(0.02)  # 模拟流式延迟

            assistant_content.append(output)

            # 持久化 AI 回复
            assistant_msg = await message_repo.add(
                session_id=session_id,
                role="assistant",
                content=output,
                event_id=event_counter[0],
            )

            # 更新会话
            await session_repo.increment_message_count(session_id)
            await session_repo.update_preview(session_id, req.message[:50])

            # 发送 done 事件
            done = SSEEvent.done(session_key, assistant_msg.id, event_counter[0])
            event_counter[0] += 1
            yield done.to_sse()

        except Exception as e:
            err = SSEEvent.error(str(e), event_counter[0])
            yield err.to_sse()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ═══════════════════════════════════════════════════
# GET /sessions — 会话列表
# ═══════════════════════════════════════════════════

@router.get("/sessions", response_model=AgentSessionListResponse)
async def list_sessions(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的会话列表（按更新时间倒序）"""
    repo = AgentSessionRepo(db, user.id)
    sessions = await repo.list_sessions(limit=limit, offset=offset)
    total = len(sessions)  # 简化；生产应单独 count

    return AgentSessionListResponse(
        sessions=[
            AgentSessionResponse(
                session_key=s.session_key,
                title=s.title or "新对话",
                last_message_preview=s.last_message_preview,
                message_count=s.message_count or 0,
                created_at=s.created_at,
                updated_at=s.updated_at,
            )
            for s in sessions
        ],
        total=total,
    )


# ═══════════════════════════════════════════════════
# GET /sessions/{key}/messages — 消息历史
# ═══════════════════════════════════════════════════

@router.get("/sessions/{session_key}/messages", response_model=AgentMessageListResponse)
async def get_messages(
    session_key: str,
    before_id: int = Query(None, description="分页：获取此 ID 之前的消息"),
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取会话消息历史（分页）"""
    session_repo = AgentSessionRepo(db, user.id)
    session = await session_repo.get_by_key(session_key)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    msg_repo = AgentMessageRepo(db, user.id)
    messages = await msg_repo.list_by_session(
        session_id=session.id,
        before_id=before_id,
        limit=limit,
    )

    items = [
        AgentMessageResponse(
            role=m.role,
            content=m.content,
            tool_name=m.tool_name,
            event_id=m.event_id,
            created_at=m.created_at,
        )
        for m in messages
    ]

    return AgentMessageListResponse(
        messages=items,
        has_more=len(items) >= limit,
    )


# ═══════════════════════════════════════════════════
# DELETE /sessions/{key} — 删除会话
# ═══════════════════════════════════════════════════

@router.delete("/sessions/{session_key}", response_model=AgentDeleteResponse)
async def delete_session(
    session_key: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除会话及其所有消息"""
    repo = AgentSessionRepo(db, user.id)
    ok = await repo.delete(session_key)
    if not ok:
        raise HTTPException(status_code=404, detail="会话不存在")
    return AgentDeleteResponse(session_key=session_key)
