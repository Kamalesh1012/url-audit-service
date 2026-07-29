"""Read-through cache for audit results, keyed by normalized URL hash."""
import hashlib
import json
from typing import Optional, Protocol

from app.config import settings
from app.models.response import AuditResult


def cache_key(url: str) -> str:
    return "audit:" + hashlib.sha256(url.encode()).hexdigest()


class CacheBackend(Protocol):
    async def get(self, key: str) -> Optional[str]: ...
    async def set(self, key: str, value: str, ex: int) -> None: ...


class RedisCache:
    def __init__(self, redis_url: str = settings.redis_url):
        import redis.asyncio as redis
        self._client = redis.from_url(redis_url, decode_responses=True)

    async def get(self, key: str) -> Optional[str]:
        return await self._client.get(key)

    async def set(self, key: str, value: str, ex: int) -> None:
        await self._client.set(key, value, ex=ex)


class AuditCache:
    def __init__(self, backend: CacheBackend, ttl_seconds: int = settings.cache_ttl_seconds):
        self.backend = backend
        self.ttl_seconds = ttl_seconds

    async def get(self, url: str) -> Optional[AuditResult]:
        raw = await self.backend.get(cache_key(url))
        if raw is None:
            return None
        data = json.loads(raw)
        data["from_cache"] = True
        return AuditResult(**data)

    async def set(self, url: str, result: AuditResult) -> None:
        payload = result.model_dump(mode="json")
        payload["from_cache"] = False
        await self.backend.set(cache_key(url), json.dumps(payload), ex=self.ttl_seconds)
