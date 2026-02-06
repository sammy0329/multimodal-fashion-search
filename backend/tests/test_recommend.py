"""추천 API 통합 테스트."""

import json
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from app.services.cache import CacheService
from app.services.recommend import RecommendService


@pytest.fixture
def mock_recommend_service() -> AsyncMock:
    """목 RecommendService."""
    service = AsyncMock(spec=RecommendService)
    service.generate_comment = AsyncMock(
        return_value="이 상품은 캐주얼한 스타일로 데일리룩에 적합합니다."
    )

    async def mock_stream(*args, **kwargs):
        for chunk in ["이 상품은 ", "캐주얼한 ", "스타일입니다."]:
            yield chunk

    service.generate_comment_stream = mock_stream
    return service


@pytest.fixture
def mock_cache_service() -> AsyncMock:
    """목 CacheService (캐시 미스)."""
    service = AsyncMock(spec=CacheService)
    service.get = AsyncMock(return_value=None)
    service.set = AsyncMock(return_value=None)
    return service


@pytest.fixture
def client_with_mocks(
    client: AsyncClient,
    mock_recommend_service: AsyncMock,
    mock_cache_service: AsyncMock,
) -> AsyncClient:
    """목 서비스가 주입된 클라이언트."""
    client._transport.app.state.recommend_service = mock_recommend_service
    client._transport.app.state.cache_service = mock_cache_service
    return client


class TestRecommendValidation:
    """입력 검증 테스트."""

    async def test_empty_product_ids_returns_422(
        self, client_with_mocks: AsyncClient
    ) -> None:
        """빈 product_ids는 422를 반환한다."""
        response = await client_with_mocks.post(
            "/api/v1/recommend",
            json={"product_ids": []},
        )

        assert response.status_code == 422

    async def test_too_many_product_ids_returns_422(
        self, client_with_mocks: AsyncClient
    ) -> None:
        """product_ids가 10개 초과면 422를 반환한다."""
        response = await client_with_mocks.post(
            "/api/v1/recommend",
            json={"product_ids": [f"p{i:03d}" for i in range(11)]},
        )

        assert response.status_code == 422

    async def test_missing_product_ids_returns_422(
        self, client_with_mocks: AsyncClient
    ) -> None:
        """product_ids가 없으면 422를 반환한다."""
        response = await client_with_mocks.post(
            "/api/v1/recommend",
            json={},
        )

        assert response.status_code == 422


class TestRecommendJSON:
    """JSON 응답 모드 테스트."""

    async def test_returns_recommend_response(
        self, client_with_mocks: AsyncClient
    ) -> None:
        """정상 요청 시 RecommendResponse를 반환한다."""
        response = await client_with_mocks.post(
            "/api/v1/recommend",
            json={"product_ids": ["p001"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert "comment" in data
        assert "product_ids" in data
        assert data["product_ids"] == ["p001"]

    async def test_with_user_query(
        self, client_with_mocks: AsyncClient,
        mock_recommend_service: AsyncMock,
    ) -> None:
        """user_query가 서비스에 전달된다."""
        await client_with_mocks.post(
            "/api/v1/recommend",
            json={"product_ids": ["p001"], "user_query": "오버핏 셔츠"},
        )

        mock_recommend_service.generate_comment.assert_called_once_with(
            product_ids=["p001"],
            user_query="오버핏 셔츠",
        )

    async def test_cache_hit_returns_cached(
        self,
        client_with_mocks: AsyncClient,
        mock_cache_service: AsyncMock,
        mock_recommend_service: AsyncMock,
    ) -> None:
        """캐시 히트 시 캐시된 응답을 반환하고 LLM을 호출하지 않는다."""
        mock_cache_service.get.return_value = {
            "comment": "캐시된 코멘트",
            "product_ids": ["p001"],
        }

        response = await client_with_mocks.post(
            "/api/v1/recommend",
            json={"product_ids": ["p001"]},
        )

        assert response.status_code == 200
        assert response.json()["comment"] == "캐시된 코멘트"
        mock_recommend_service.generate_comment.assert_not_called()

    async def test_cache_miss_stores_result(
        self,
        client_with_mocks: AsyncClient,
        mock_cache_service: AsyncMock,
    ) -> None:
        """캐시 미스 시 결과를 캐시에 저장한다."""
        await client_with_mocks.post(
            "/api/v1/recommend",
            json={"product_ids": ["p001"]},
        )

        mock_cache_service.set.assert_called_once()
        call_args = mock_cache_service.set.call_args
        assert "comment" in call_args[0][1]

    async def test_value_error_returns_400(
        self,
        client_with_mocks: AsyncClient,
        mock_recommend_service: AsyncMock,
    ) -> None:
        """ValueError 발생 시 400을 반환한다."""
        mock_recommend_service.generate_comment.side_effect = ValueError(
            "상품을 찾을 수 없습니다"
        )

        response = await client_with_mocks.post(
            "/api/v1/recommend",
            json={"product_ids": ["p999"]},
        )

        assert response.status_code == 400
        assert "상품을 찾을 수 없습니다" in response.json()["detail"]

    async def test_runtime_error_returns_503(
        self,
        client_with_mocks: AsyncClient,
        mock_recommend_service: AsyncMock,
    ) -> None:
        """RuntimeError 발생 시 503을 반환한다."""
        mock_recommend_service.generate_comment.side_effect = RuntimeError(
            "LLM 오류"
        )

        response = await client_with_mocks.post(
            "/api/v1/recommend",
            json={"product_ids": ["p001"]},
        )

        assert response.status_code == 503
        assert "추천 서비스 일시 장애" in response.json()["detail"]


class TestRecommendStream:
    """SSE 스트리밍 모드 테스트."""

    async def test_stream_returns_sse(
        self, client_with_mocks: AsyncClient
    ) -> None:
        """stream=true 시 SSE 응답을 반환한다."""
        response = await client_with_mocks.post(
            "/api/v1/recommend?stream=true",
            json={"product_ids": ["p001"]},
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    async def test_stream_yields_delta_events(
        self, client_with_mocks: AsyncClient
    ) -> None:
        """스트리밍 시 delta 이벤트를 순서대로 반환한다."""
        response = await client_with_mocks.post(
            "/api/v1/recommend?stream=true",
            json={"product_ids": ["p001"]},
        )

        content = response.text
        lines = [line for line in content.split("\n") if line.startswith("data:")]

        # delta 이벤트 확인
        delta_events = []
        for line in lines:
            data = json.loads(line[5:].strip())
            if data["event"] == "delta":
                delta_events.append(data["data"])

        assert "이 상품은 " in delta_events
        assert "캐주얼한 " in delta_events
        assert "스타일입니다." in delta_events

    async def test_stream_ends_with_done(
        self, client_with_mocks: AsyncClient
    ) -> None:
        """스트리밍은 done 이벤트로 종료된다."""
        response = await client_with_mocks.post(
            "/api/v1/recommend?stream=true",
            json={"product_ids": ["p001"]},
        )

        content = response.text
        lines = [line for line in content.split("\n") if line.startswith("data:")]

        # 마지막 이벤트가 done인지 확인
        last_event = json.loads(lines[-1][5:].strip())
        assert last_event["event"] == "done"

    async def test_stream_value_error_yields_error_event(
        self,
        client_with_mocks: AsyncClient,
        mock_recommend_service: AsyncMock,
    ) -> None:
        """스트리밍 중 ValueError 발생 시 error 이벤트를 반환한다."""

        async def error_stream(*args, **kwargs):
            raise ValueError("상품을 찾을 수 없습니다")
            yield  # noqa: unreachable

        mock_recommend_service.generate_comment_stream = error_stream

        response = await client_with_mocks.post(
            "/api/v1/recommend?stream=true",
            json={"product_ids": ["p999"]},
        )

        content = response.text
        lines = [line for line in content.split("\n") if line.startswith("data:")]

        # error 이벤트 확인
        has_error = False
        for line in lines:
            data = json.loads(line[5:].strip())
            if data["event"] == "error":
                has_error = True
                assert "상품을 찾을 수 없습니다" in data["data"]

        assert has_error

    async def test_stream_runtime_error_yields_generic_error(
        self,
        client_with_mocks: AsyncClient,
        mock_recommend_service: AsyncMock,
    ) -> None:
        """스트리밍 중 RuntimeError 발생 시 일반 에러 메시지를 반환한다."""

        async def error_stream(*args, **kwargs):
            raise RuntimeError("LLM 오류")
            yield  # noqa: unreachable

        mock_recommend_service.generate_comment_stream = error_stream

        response = await client_with_mocks.post(
            "/api/v1/recommend?stream=true",
            json={"product_ids": ["p001"]},
        )

        content = response.text
        lines = [line for line in content.split("\n") if line.startswith("data:")]

        # 일반 에러 메시지 확인
        has_error = False
        for line in lines:
            data = json.loads(line[5:].strip())
            if data["event"] == "error":
                has_error = True
                assert "추천 서비스 일시 장애" in data["data"]

        assert has_error

    async def test_stream_no_cache_headers(
        self, client_with_mocks: AsyncClient
    ) -> None:
        """스트리밍 응답에 캐시 방지 헤더가 포함된다."""
        response = await client_with_mocks.post(
            "/api/v1/recommend?stream=true",
            json={"product_ids": ["p001"]},
        )

        assert response.headers["cache-control"] == "no-cache"
        assert response.headers["connection"] == "keep-alive"
