# schemas.py — Pydantic 请求/响应模型
from pydantic import BaseModel, Field, field_validator
from typing import Optional
import re


# --- 请求模型 ---

class UserRegisterRequest(BaseModel):
    """用户注册"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=128, description="密码")
    email: Optional[str] = Field(None, max_length=255, description="邮箱")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("用户名只能包含字母、数字和下划线")
        return v


class UserLoginRequest(BaseModel):
    """用户登录"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class TokenRefreshRequest(BaseModel):
    """刷新 Token"""
    refresh_token: str = Field(..., description="Refresh Token")


class BindCredentialRequest(BaseModel):
    """绑定教务凭证"""
    student_no: str = Field(..., min_length=1, max_length=30, description="学号")
    login_account: str = Field(..., min_length=1, max_length=100, description="教务登录账号")
    password: str = Field(..., min_length=1, max_length=128, description="教务密码")
    base_url: str = Field("https://jwglxt.buct.edu.cn", description="教务系统地址")
    doubao_api_key: Optional[str] = Field(None, max_length=256, description="豆包 API Key")


# --- 响应模型 ---

class TokenResponse(BaseModel):
    """Token 响应"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """用户信息响应"""
    id: str
    username: str
    email: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool
    has_credential: bool = False  # 是否已绑定教务凭证

    model_config = {"from_attributes": True}


class CredentialStatusResponse(BaseModel):
    """凭证状态响应"""
    is_bound: bool
    student_no: Optional[str] = None
    is_valid: Optional[bool] = None
    last_sync_at: Optional[str] = None


class MessageResponse(BaseModel):
    """通用消息响应"""
    message: str
