# credentials.py — 教务凭证管理 API: 绑定 / 状态 / 解绑
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.session import get_db
from app.database.models import User, EduCredential
from app.auth.schemas import (
    BindCredentialRequest, CredentialStatusResponse, MessageResponse,
)
from app.auth.security import encrypt_credential
from app.auth.dependencies import get_current_user

router = APIRouter()


@router.post("/bind", response_model=MessageResponse)
async def bind_credential(
    req: BindCredentialRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """绑定教务凭证 — 加密存储学号和教务密码"""
    # 检查是否已绑定
    result = await db.execute(
        select(EduCredential).where(EduCredential.user_id == user.id)
    )
    existing = result.scalar_one_or_none()

    if existing and existing.is_valid:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="已绑定教务凭证，请先解绑",
        )

    # 加密教务密码和豆包 Key
    encrypted_pwd = encrypt_credential(req.password)
    encrypted_doubao = (
        encrypt_credential(req.doubao_api_key) if req.doubao_api_key else None
    )

    if existing:
        # 更新现有凭证
        existing.student_no = req.student_no
        existing.login_account = req.login_account
        existing.encrypted_password = encrypted_pwd
        existing.base_url = req.base_url
        existing.doubao_api_key = encrypted_doubao
        existing.doubao_model = None
        existing.is_valid = True
    else:
        # 新建凭证
        cred = EduCredential(
            user_id=user.id,
            student_no=req.student_no,
            login_account=req.login_account,
            encrypted_password=encrypted_pwd,
            base_url=req.base_url,
            doubao_api_key=encrypted_doubao,
        )
        db.add(cred)

    await db.commit()
    return MessageResponse(message="教务凭证绑定成功")


@router.get("/status", response_model=CredentialStatusResponse)
async def credential_status(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """查询当前用户的教务凭证状态"""
    result = await db.execute(
        select(EduCredential).where(EduCredential.user_id == user.id)
    )
    cred = result.scalar_one_or_none()

    if cred is None:
        return CredentialStatusResponse(is_bound=False)

    return CredentialStatusResponse(
        is_bound=True,
        student_no=cred.student_no,
        is_valid=cred.is_valid,
        last_sync_at=cred.last_sync_at.isoformat() if cred.last_sync_at else None,
    )


@router.delete("/unbind", response_model=MessageResponse)
async def unbind_credential(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """解绑教务凭证 — 软删除（标记为无效），不删除历史数据"""
    result = await db.execute(
        select(EduCredential).where(EduCredential.user_id == user.id)
    )
    cred = result.scalar_one_or_none()

    if cred is None or not cred.is_valid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到有效凭证",
        )

    cred.is_valid = False
    await db.commit()
    return MessageResponse(message="教务凭证已解绑")
