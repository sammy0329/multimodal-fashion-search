"""Redis 비동기 캐싱 서비스.

검색 결과를 JSON 직렬화하여 TTL 기반으로 캐싱한다.
"""

import hashlib
import json
import logging
from typing import Any

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

DEFAULT_TTL = 3600


class CacheService:
    """Redis 기반 비동기 캐시 서비스.

    Args:
        redis_client: redis.asyncio 클라이언트 인스턴스.
    """

    def __init__(self, redis_client: aioredis.Redis) -> None:
        self._redis = redis_client

    async def get(self, key: str) -> Any | None:
        """캐시에서 값을 조회한다.

        Args:
            key: 캐시 키.

        Returns:
            캐시된 값 (dict/list) 또는 None.
        """
        try:
            data = await self._redis.get(key)
            if data is None:
                return None
            return json.loads(data)
        except Exception:
            logger.warning("캐시 조회 실패 (key=%s)", key, exc_info=True)
            return None

    async def set(self, key: str, value: Any, ttl: int = DEFAULT_TTL) -> None:
        """캐시에 값을 저장한다.

        Args:
            key: 캐시 키.
            value: JSON 직렬화 가능한 값.
            ttl: TTL (초). 기본 3600초.
        """
        try:
            serialized = json.dumps(value, ensure_ascii=False, default=str)
            await self._redis.set(key, serialized, ex=ttl)
        except Exception:
            logger.warning("캐시 저장 실패 (key=%s)", key, exc_info=True)

    async def close(self) -> None:
        """Redis 연결을 닫는다."""
        await self._redis.close()

    @staticmethod
    def build_cache_key(request_data: dict) -> str:
        """요청 데이터로 캐시 키를 생성한다.

        Args:
            request_data: 요청 JSON 딕셔너리.

        Returns:
            "search:" 접두사 + MD5 해시 키.
        """
        serialized = json.dumps(request_data, sort_keys=True, ensure_ascii=False)
        digest = hashlib.md5(serialized.encode()).hexdigest()
        return f"search:{digest}"
