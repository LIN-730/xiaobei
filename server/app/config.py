# config.py — 环境变量配置
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置，从环境变量/.env文件读取"""

    # --- 应用 ---
    APP_NAME: str = "教务智能助手"
    DEBUG: bool = False
    CORS_ORIGINS: str = "*"

    # --- 数据库 ---
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "edu_assistant"
    POSTGRES_USER: str = "edu_user"
    POSTGRES_PASSWORD: str = "change_me"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def DATABASE_URL_SYNC(self) -> str:
        """Alembic 迁移用的同步URL"""
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # --- Redis ---
    REDIS_URL: str = "redis://localhost:6379/0"

    # --- JWT ---
    JWT_SECRET_KEY: str = "change_me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- AES 凭证加密 ---
    CREDENTIAL_ENCRYPTION_KEY: str = "change_me"

    # --- LLM ---
    DOUBAO_BASE_URL: str = "https://ark.cn-beijing.volces.com/api/v3"
    DOUBAO_DEFAULT_API_KEY: Optional[str] = None
    DOUBAO_DEFAULT_MODEL: str = "deepseek-v4-pro"

    # --- 教务系统 ---
    EDU_BASE_URL: str = "https://jwglxt.buct.edu.cn"

    # --- ChromaDB ---
    CHROMA_PERSIST_DIR: str = "/app/data/chroma"

    model_config = {"env_file": ".env", "case_sensitive": True, "extra": "ignore"}


settings = Settings()
