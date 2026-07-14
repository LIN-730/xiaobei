# API v1 路由聚合
from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.credentials import router as credentials_router
from app.api.v1.courses import router as courses_router
from app.api.v1.scores import router as scores_router
from app.api.v1.exams import router as exams_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.sync import router as sync_router
from app.api.v1.agent import router as agent_router
from app.api.v1.planning import router as planning_router
from app.api.v1.knowledge import router as knowledge_router
from app.api.v1.classrooms import router as classrooms_router
from app.api.v1.notifications import router as notifications_router

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(auth_router, prefix="/auth", tags=["认证"])
v1_router.include_router(credentials_router, prefix="/credentials", tags=["教务凭证"])
v1_router.include_router(courses_router, prefix="/courses", tags=["课表"])
v1_router.include_router(scores_router, prefix="/scores", tags=["成绩"])
v1_router.include_router(exams_router, prefix="/exams", tags=["考试"])
v1_router.include_router(dashboard_router, prefix="/dashboard", tags=["仪表盘"])
v1_router.include_router(sync_router, prefix="/sync", tags=["同步"])
v1_router.include_router(agent_router, prefix="/agent", tags=["AI对话"])
v1_router.include_router(planning_router, prefix="/planning", tags=["学业规划"])
v1_router.include_router(knowledge_router, prefix="/knowledge", tags=["知识库"])
v1_router.include_router(classrooms_router, prefix="/classrooms", tags=["空闲教室"])
v1_router.include_router(notifications_router, prefix="/notifications", tags=["通知"])
