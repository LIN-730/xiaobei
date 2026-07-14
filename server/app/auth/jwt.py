# jwt.py — JWT 令牌生成与验证
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from app.config import settings


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(user_id: str) -> str:
    """生成 Access Token (短期，默认30分钟)"""
    now = _utcnow()
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "type": "access",
        "exp": expire,
        "iat": now,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """生成 Refresh Token (长期，默认7天)"""
    now = _utcnow()
    expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": user_id,
        "type": "refresh",
        "exp": expire,
        "iat": now,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def verify_token(token: str, expected_type: str = "access") -> dict:
    """验证 JWT 令牌，返回 payload。无效或过期抛出异常。"""
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    token_type = payload.get("type")
    if token_type != expected_type:
        raise JWTError(f"Token type mismatch: expected {expected_type}, got {token_type}")
    return payload


def get_user_id_from_token(token: str) -> str:
    """从有效 JWT 中提取 user_id"""
    payload = verify_token(token, expected_type="access")
    return payload["sub"]
