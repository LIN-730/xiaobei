# celery_app.py — Celery 应用配置
import os
from celery import Celery
from app.config import settings

# Docker 环境中 Redis 地址可能不同（容器内 redis://redis:6379 而非 localhost）
BROKER_URL = os.getenv("CELERY_BROKER_URL", settings.REDIS_URL)
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", settings.REDIS_URL)

celery_app = Celery(
    "edu_assistant",
    broker=BROKER_URL,
    backend=RESULT_BACKEND,
    include=["app.sync.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=300,
    task_time_limit=600,
    worker_max_tasks_per_child=50,
)
