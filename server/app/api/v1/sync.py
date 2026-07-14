# sync.py — 同步触发/状态 API
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.database.repositories.repos import SyncLogRepo
from app.auth.dependencies import get_current_user
from app.database.models import User
# Celery tasks 懒加载（FastAPI 不依赖 Celery worker）
def _get_sync_user_all():
    from app.sync.tasks import sync_user_all
    return sync_user_all

router = APIRouter()


@router.post("/trigger")
async def trigger_sync(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """触发当前用户全量数据同步 — 异步执行"""
    # 检查是否有正在进行的同步
    log_repo = SyncLogRepo(db, user.id)
    latest = await log_repo.get_latest()
    if latest and latest.status == "running":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="同步正在进行中",
        )

    # 提交 Celery 任务
    sync_user_all = _get_sync_user_all()
    task = sync_user_all.delay(user.id)
    return {
        "message": "同步任务已提交",
        "task_id": task.id,
    }


@router.get("/status")
async def get_sync_status(
    module: str = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """查询同步状态"""
    log_repo = SyncLogRepo(db, user.id)
    log = await log_repo.get_latest(module=module)

    if log is None:
        return {"status": "never_synced"}

    return {
        "status": log.status,
        "module": log.module,
        "record_count": log.record_count,
        "error_msg": log.error_msg,
        "started_at": log.started_at.isoformat() if log.started_at else None,
        "completed_at": log.completed_at.isoformat() if log.completed_at else None,
    }
