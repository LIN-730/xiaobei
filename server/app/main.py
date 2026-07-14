# main.py — FastAPI 应用入口
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1 import v1_router
from app.database.session import engine, Base


@asynccontextmanager                                                      
async def lifespan(app: FastAPI):                       
    """应用生命周期 — 启动时创建数据库表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="北京化工大学教务智能助手 — 多用户后端 API",
    lifespan=lifespan,
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(v1_router, prefix="/api")


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "ok", "app": settings.APP_NAME}
