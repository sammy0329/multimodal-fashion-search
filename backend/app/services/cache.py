from typing import Any


class CacheService:
    """Redis 캐싱 서비스. M3에서 구현 예정."""

    async def get(self, key: str) -> Any | None:
        """캐시에서 값 조회."""
        raise NotImplementedError("M3에서 구현 예정")

    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """캐시에 값 저장."""
        raise NotImplementedError("M3에서 구현 예정")
