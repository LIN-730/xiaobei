# tests/conftest.py — pytest 测试基础设施
"""提供 async DB session / FastAPI test client / auth headers 等 fixtures"""
import os
import sys
import pytest
import asyncio
from typing import AsyncGenerator, Optional

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ---- 测试数据库 URL ----
# 优先使用 TEST_DATABASE_URL 环境变量，否则用 .env 中的配置
_test_db = os.getenv("TEST_DATABASE_URL", "")
if not _test_db:
    from app.config import settings
    _test_db = settings.DATABASE_URL

TEST_DATABASE_URL = _test_db


@pytest.fixture(scope="session")
def event_loop():
    """会话级事件循环"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """会话级异步引擎 — 创建所有表，测试结束后清理"""
    from sqlalchemy.ext.asyncio import create_async_engine
    from app.database.session import Base
    # 导入 models 确保所有表注册到 Base.metadata
    import app.database.models  # noqa: F401

    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator:
    """每个测试函数独立的数据库会话（自动回滚）"""
    from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

    session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        async with session.begin():
            yield session
            await session.rollback()


@pytest.fixture
async def client() -> AsyncGenerator:
    """FastAPI 异步测试客户端（httpx.AsyncClient + ASGITransport）"""
    from httpx import ASGITransport, AsyncClient
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def auth_headers(client, db_session) -> dict:
    """认证请求头 — 注册新用户并返回 Bearer Token"""
    from app.database.models import User
    from app.auth.security import hash_password

    # 直接在数据库中创建用户（跳过注册 API 的依赖）
    import uuid
    user = User(
        id=str(uuid.uuid4()),
        username=f"testuser_{uuid.uuid4().hex[:8]}",
        password_hash=hash_password("testpass123"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    # 生成 JWT Token
    from app.auth.jwt import create_access_token
    token = create_access_token(user.id)

    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def test_user_id(auth_headers) -> Optional[str]:
    """从 auth_headers 中提取测试用户 ID"""
    from app.auth.jwt import verify_token
    token = auth_headers["Authorization"].replace("Bearer ", "")
    payload = verify_token(token, expected_type="access")
    return payload["sub"]
