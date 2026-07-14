# session_pool.py — Redis 缓存的教务系统 Session 池
import pickle
import redis.asyncio as aioredis
from app.config import settings

SESSION_TTL = 600  # 10 分钟过期
KEY_PREFIX = "edu_session:"


class SessionPool:
    """教务系统 Session 池 — Redis 缓存 + 自动过期"""

    def __init__(self, redis_url: str = None):
        self.redis = aioredis.from_url(
            redis_url or settings.REDIS_URL,
            decode_responses=False,  # 不自动解码，因为存储的是 pickle 二进制
        )

    def _key(self, user_id: str) -> str:
        return f"{KEY_PREFIX}{user_id}"

    async def get(self, user_id: str):
        """获取缓存的 Session，不存在返回 None"""
        data = await self.redis.get(self._key(user_id))
        if data is None:
            return None
        try:
            return pickle.loads(data)
        except Exception:
            await self.invalidate(user_id)
            return None

    async def set(self, user_id: str, session):
        """缓存 Session，TTL 10 分钟"""
        await self.redis.setex(
            self._key(user_id),
            SESSION_TTL,
            pickle.dumps(session),
        )

    async def invalidate(self, user_id: str):
        """删除缓存的 Session"""
        await self.redis.delete(self._key(user_id))

    async def has(self, user_id: str) -> bool:
        """检查是否有缓存"""
        return await self.redis.exists(self._key(user_id)) > 0

    async def close(self):
        """关闭连接"""
        await self.redis.aclose()


# 全局单例
session_pool = SessionPool()
