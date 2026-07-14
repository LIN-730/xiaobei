# agent_manager.py — per-user AgentExecutor 池 (P3)
"""
管理用户级 Agent 实例：
- 30 分钟 TTL 缓存
- LLM API Key: EduCredential 优先，settings 回退
- 每个用户独立 Tools + AgentExecutor
"""
from __future__ import annotations

import time
import threading
from typing import Optional, Dict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from langchain.agents import AgentExecutor
from langchain.agents.openai_tools.base import convert_to_openai_tool, format_to_openai_tool_messages
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from langchain_openai import ChatOpenAI

from app.config import settings
from app.database.models import EduCredential
from app.auth.security import _get_fernet
from app.agent.tools import create_tools
from app.agent.user_profile import get_time_context
from app.agent.edu_knowledge import BUCT_EDU_KNOWLEDGE


# ═══════════════════════════════════════════════════
# Agent 缓存
# ═══════════════════════════════════════════════════

_agent_cache: Dict[str, dict] = {}  # user_id → {"executor": ..., "created_at": float}
_cache_lock = threading.Lock()
AGENT_TTL = 30 * 60  # 30 分钟


def _evict_expired():
    """清理过期缓存"""
    now = time.time()
    with _cache_lock:
        expired = [uid for uid, v in _agent_cache.items() if now - v["created_at"] > AGENT_TTL]
        for uid in expired:
            del _agent_cache[uid]


# ═══════════════════════════════════════════════════
# LLM 工厂
# ═══════════════════════════════════════════════════

async def _get_llm_config(db: AsyncSession, user_id: str) -> dict:
    """
    获取用户的 LLM 配置。
    优先级: EduCredential.doubao_api_key (解密) > settings
    """
    # 1. 尝试从用户凭证获取
    stmt = select(EduCredential).where(EduCredential.user_id == user_id)
    result = await db.execute(stmt)
    cred = result.scalar_one_or_none()

    if cred and cred.doubao_api_key:
        try:
            api_key = _get_fernet().decrypt(cred.doubao_api_key.encode()).decode()
        except Exception:
            api_key = None

        model = cred.doubao_model or settings.DOUBAO_DEFAULT_MODEL
        if api_key:
            return {
                "api_key": api_key,
                "model": model,
                "base_url": settings.DOUBAO_BASE_URL,
            }

    # 2. 回退到 settings
    return {
        "api_key": settings.DOUBAO_DEFAULT_API_KEY or "",
        "model": settings.DOUBAO_DEFAULT_MODEL,
        "base_url": settings.DOUBAO_BASE_URL,
    }


def _build_llm(config: dict) -> ChatOpenAI:
    """创建 LLM 实例"""
    return ChatOpenAI(
        model=config["model"],
        api_key=config["api_key"],
        base_url=config["base_url"],
        temperature=0.3,
        max_tokens=2000,
        timeout=30,
        max_retries=2,
    )


# ═══════════════════════════════════════════════════
# Prompt
# ═══════════════════════════════════════════════════

def _build_prompt() -> ChatPromptTemplate:
    ctx = get_time_context()
    system = f"""你是北京化工大学学生的专属AI助手"小北"。你可以像朋友一样自然聊天，也能查教务数据。

## 时间上下文
{ctx}
- 用户问「这周」「最近」「当前学期」时，默认使用上述学期
- "上学期""下学期"根据当前学期推算

## 你的能力
- 友好、有温度，像学长/学姐一样自然对话
- 知识面广：学习、编程、生活、科技都能聊
- 对北化教务了如指掌：任何功能在哪、怎么操作都知道
- 查个人教务数据：课表/成绩/考试/学分/通知/文件等

## 北化教务速查
{BUCT_EDU_KNOWLEDGE}

## 可用工具（仅当明确需要个人数据时调用）
- query_courses: 课表(默认当前学期本周)
- query_scores: 成绩(默认全学期)
- query_exams: 考试(默认当前学期)
- query_student_info: 个人基本信息
- query_academic_status: 学分进度/GPA
- query_warnings: 学籍预警
- query_training_plan: 培养方案
- query_selected_courses: 已选课程
- query_classrooms: 空闲教室(可筛星期/教学楼)
- query_notifications: 搜通知/文件/消息(category/keyword可选)
- search_knowledge_base: 搜已上传文档
- query_edu_guide: 教务操作指南(怎么查成绩/在哪选课等)
- list_knowledge_files: 列出知识库文件
- analyze_credit_gap: 📊 学分缺口分析(模块组进度/缺哪些课)
- check_required_courses: 📋 必修课检查(哪些必修还没修/未通过)
- recommend_courses: 📚 选课推荐(基于缺口推荐下学期选什么课)
- plan_academic_path: 🗓️ 学业路径规划(每学期安排/毕业前如何修完)

## 规则
- 教务数据必须用工具获取，禁止编造
- 参数不明确时追问一句
- 回答自然简洁，不啰嗦"""

    return ChatPromptTemplate.from_messages([
        ("system", system),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])


# ═══════════════════════════════════════════════════
# AgentExecutor 构建器
# ═══════════════════════════════════════════════════

def _build_agent_executor(llm: ChatOpenAI, tools: list) -> AgentExecutor:
    """构建 AgentExecutor"""
    prompt = _build_prompt()
    openai_tools = [convert_to_openai_tool(t) for t in tools]
    llm_with_tools = llm.bind(tools=openai_tools)

    def _assign_scratchpad(x: dict) -> dict:
        return {**x, "agent_scratchpad": format_to_openai_tool_messages(x["intermediate_steps"])}

    agent = (
        RunnableLambda(_assign_scratchpad)
        | prompt
        | llm_with_tools
        | OpenAIToolsAgentOutputParser()
    )
    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=False,
        handle_parsing_errors=True,
        max_iterations=5,
    )


# ═══════════════════════════════════════════════════
# 公开 API
# ═══════════════════════════════════════════════════

async def get_or_create_agent(
    db: AsyncSession,
    user_id: str,
    student_no: str = "",
    upload_dir: Optional[str] = None,
) -> AgentExecutor:
    """
    获取或创建用户的 AgentExecutor（带 30min TTL 缓存）。

    Args:
        db: 异步数据库会话
        user_id: 用户 UUID
        student_no: 学号
        upload_dir: 知识库文件上传目录（可选）

    Returns:
        AgentExecutor 实例
    """
    _evict_expired()

    with _cache_lock:
        cached = _agent_cache.get(user_id)
        if cached:
            # 检查是否过期
            if time.time() - cached["created_at"] < AGENT_TTL:
                return cached["executor"]

    # 构建新的 Agent
    llm_config = await _get_llm_config(db, user_id)
    llm = _build_llm(llm_config)

    # 创建 Tools (knowledge_tools 内部工厂会自动处理 RAG 初始化)
    tools = create_tools(
        db=db,
        user_id=user_id,
        student_no=student_no,
        upload_dir=upload_dir,
    )

    executor = _build_agent_executor(llm, tools)

    with _cache_lock:
        _agent_cache[user_id] = {
            "executor": executor,
            "created_at": time.time(),
        }

    return executor


def invalidate_agent(user_id: str) -> None:
    """清除用户缓存的 Agent（API Key 更新后调用）"""
    with _cache_lock:
        _agent_cache.pop(user_id, None)


def get_cache_stats() -> dict:
    """获取缓存统计（调试用）"""
    _evict_expired()
    with _cache_lock:
        return {
            "cached_agents": len(_agent_cache),
            "users": list(_agent_cache.keys()),
        }
