"""CacheService 유닛 테스트.

Redis를 mock하여 캐싱 로직만 검증한다.
"""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.cache import CacheService


@pytest.fixture
def mock_redis():
    """Mock Redis 클라이언트."""
    redis = AsyncMock()
    return redis


@pytest.fixture
def cache_service(mock_redis):
    """Mock Redis로 초기화된 CacheService."""
    return CacheService(redis_client=mock_redis)


class TestGet:
    async def test_returns_parsed_json(self, cache_service, mock_redis):
        data = {"results": [{"id": "1"}], "total": 1}
        mock_redis.get.return_value = json.dumps(data)

        result = await cache_service.get("search:abc123")

        assert result == data
        mock_redis.get.assert_awaited_once_with("search:abc123")

    async def test_returns_none_on_cache_miss(self, cache_service, mock_redis):
        mock_redis.get.return_value = None

        result = await cache_service.get("search:missing")

        assert result is None

    async def test_returns_none_on_error(self, cache_service, mock_redis):
        mock_redis.get.side_effect = ConnectionError("Redis down")

        result = await cache_service.get("search:error")

        assert result is None


class TestSet:
    async def test_stores_json_with_ttl(self, cache_service, mock_redis):
        data = {"results": [], "total": 0}

        await cache_service.set("search:key1", data, ttl=1800)

        mock_redis.set.assert_awaited_once()
        call_args = mock_redis.set.call_args
        assert call_args.args[0] == "search:key1"
        assert json.loads(call_args.args[1]) == data
        assert call_args.kwargs["ex"] == 1800

    async def test_uses_default_ttl(self, cache_service, mock_redis):
        await cache_service.set("search:key2", {"data": True})

        call_args = mock_redis.set.call_args
        assert call_args.kwargs["ex"] == 3600

    async def test_handles_error_gracefully(self, cache_service, mock_redis):
        mock_redis.set.side_effect = ConnectionError("Redis down")

        await cache_service.set("search:error", {"data": True})


class TestClose:
    async def test_closes_redis_connection(self, cache_service, mock_redis):
        await cache_service.close()

        mock_redis.close.assert_awaited_once()


class TestBuildCacheKey:
    def test_produces_deterministic_key(self):
        data = {"query": "셔츠", "limit": 20}
        key1 = CacheService.build_cache_key(data)
        key2 = CacheService.build_cache_key(data)

        assert key1 == key2
        assert key1.startswith("search:")

    def test_different_data_produces_different_keys(self):
        key1 = CacheService.build_cache_key({"query": "셔츠"})
        key2 = CacheService.build_cache_key({"query": "바지"})

        assert key1 != key2

    def test_key_order_independent(self):
        key1 = CacheService.build_cache_key({"a": 1, "b": 2})
        key2 = CacheService.build_cache_key({"b": 2, "a": 1})

        assert key1 == key2
