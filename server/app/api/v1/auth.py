# auth.py — 认证 API: 注册 / 登录 / 刷新 Token
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.database.session import get_db
from app.database.models import User, EduCredential
from app.auth.schemas import (
    UserRegisterRequest, UserLoginRequest, TokenRefreshRequest,
    TokenResponse, UserResponse, MessageResponse,
)
from app.auth.security import hash_password, verify_password
from app.auth.jwt import create_access_token, create_refresh_token, verify_token
from app.auth.dependencies import get_current_user

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(req: UserRegisterRequest, db: AsyncSession = Depends(get_db)):
    """用户注册 — 创建账号并返回 JWT"""
    # 检查用户名是否已存在
    result = await db.execute(select(User).where(User.username == req.username))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="用户名已被注册",
        )

    # 检查邮箱是否已存在 — 依赖数据库唯一约束，不预先 SELECT
    if req.email:
        result = await db.execute(select(User).where(User.email == req.email))
        if result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="邮箱已被使用",
            )

    # 创建用户
    user = User(
        username=req.username,
        email=req.email,
        phone=req.phone,
        password_hash=hash_password(req.password),
    )
    db.add(user)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="用户名或邮箱已被注册",
        )
    await db.refresh(user)

    # 生成 Token
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=TokenResponse)
async def login(req: UserLoginRequest, db: AsyncSession = Depends(get_db)):
    """用户登录 — 验证用户名密码并返回 JWT"""
    result = await db.execute(select(User).where(User.username == req.username))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用",
        )

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    req: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """刷新 Access Token — 使用 Refresh Token 获取新的 Token 对"""
    try:
        payload = verify_token(req.refresh_token, expected_type="refresh")
        user_id = payload["sub"]
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh Token 无效或已过期",
        )

    # 验证用户是否仍然有效（未被禁用/删除）
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用",
        )

    access_token = create_access_token(user_id)
    new_refresh_token = create_refresh_token(user_id)

    return TokenResponse(access_token=access_token, refresh_token=new_refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """获取当前登录用户信息"""
    # 检查是否已绑定教务凭证
    result = await db.execute(
        select(EduCredential).where(EduCredential.user_id == user.id)
    )
    cred = result.scalar_one_or_none()
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        phone=user.phone,
        is_active=user.is_active,
        has_credential=cred is not None and cred.is_valid,
    )
