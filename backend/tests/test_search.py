"""검색 엔드포인트 통합 테스트.

서비스를 mock하여 /search 엔드포인트의 전체 흐름을 검증한다.
"""

import base64
import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from PIL import Image

from app.core.dependencies import (
    get_cache_service,
    get_embedding_service,
    get_search_service,
)
from app.main import app
from app.models.schemas import ProductResult

FAKE_EMBEDDING = [0.1] * 512


def _make_product_result(product_id: str, score: float = 0.9) -> ProductResult:
    return ProductResult(
        product_id=product_id,
        name=f"Product {product_id}",
        name_ko=f"상품 {product_id}",
        price=50000,
        brand="test_brand",
        category="상의",
        sub_category="셔츠",
        style_tags=["캐주얼"],
        color="화이트",
        image_url=f"https://example.com/{product_id}.jpg",
        score=score,
    )


def _make_base64_image() -> str:
    """테스트용 Base64 이미지를 생성한다."""
    image = Image.new("RGB", (224, 224), color="red")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()


@pytest.fixture
def mock_embedding_service():
    service = AsyncMock()
    service.embed_text = AsyncMock(return_value=FAKE_EMBEDDING)
    service.embed_image = AsyncMock(return_value=FAKE_EMBEDDING)
    return service


@pytest.fixture
def mock_search_service():
    service = AsyncMock()
    service.search_by_vector = AsyncMock(
        return_value=[_make_product_result("p001", 0.95)]
    )
    return service


@pytest.fixture
def mock_cache_service():
    service = AsyncMock()
    service.get = AsyncMock(return_value=None)
    service.set = AsyncMock()
    return service


@pytest.fixture
async def client(mock_embedding_service, mock_search_service, mock_cache_service):
    app.dependency_overrides[get_embedding_service] = lambda: mock_embedding_service
    app.dependency_overrides[get_search_service] = lambda: mock_search_service
    app.dependency_overrides[get_cache_service] = lambda: mock_cache_service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


class TestSearchTextQuery:
    async def test_text_search_returns_results(
        self, client, mock_embedding_service, mock_search_service
    ):
        response = await client.post(
            "/api/v1/search",
            json={"query": "오버핏 셔츠"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["query_type"] == "text"
        assert data["total"] == 1
        assert data["results"][0]["product_id"] == "p001"
        mock_embedding_service.embed_text.assert_awaited_once_with("오버핏 셔츠")

    async def test_text_search_with_filters(
        self, client, mock_search_service
    ):
        response = await client.post(
            "/api/v1/search",
            json={
                "query": "셔츠",
                "category": "상의",
                "min_price": 10000,
                "max_price": 50000,
            },
        )

        assert response.status_code == 200
        call_kwargs = mock_search_service.search_by_vector.call_args.kwargs
        filters = call_kwargs["filters"]
        assert filters["category"] == {"$eq": "상의"}
        assert filters["price"] == {"$gte": 10000, "$lte": 50000}

    async def test_text_search_respects_limit(
        self, client, mock_search_service
    ):
        response = await client.post(
            "/api/v1/search",
            json={"query": "바지", "limit": 5},
        )

        assert response.status_code == 200
        call_kwargs = mock_search_service.search_by_vector.call_args.kwargs
        assert call_kwargs["top_k"] == 5


class TestSearchImageQuery:
    async def test_image_search_returns_results(
        self, client, mock_embedding_service
    ):
        image_b64 = _make_base64_image()

        response = await client.post(
            "/api/v1/search",
            json={"image": image_b64},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["query_type"] == "image"
        mock_embedding_service.embed_image.assert_awaited_once()

    async def test_invalid_base64_returns_400(self, client):
        response = await client.post(
            "/api/v1/search",
            json={"image": "not-valid-base64!!!"},
        )

        assert response.status_code == 400


class TestSearchHybridQuery:
    async def test_hybrid_search_returns_results(
        self, client, mock_embedding_service
    ):
        image_b64 = _make_base64_image()

        with patch.object(
            type(mock_embedding_service),
            "combine_embeddings",
            staticmethod(lambda i, t, **kw: FAKE_EMBEDDING),
            create=True,
        ):
            response = await client.post(
                "/api/v1/search",
                json={"query": "레트로 드레스", "image": image_b64},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["query_type"] == "hybrid"
        mock_embedding_service.embed_text.assert_awaited_once()
        mock_embedding_service.embed_image.assert_awaited_once()


class TestSearchValidation:
    async def test_no_query_no_image_returns_400(self, client):
        response = await client.post(
            "/api/v1/search",
            json={},
        )

        assert response.status_code == 400
        assert "query 또는 image" in response.json()["detail"]

    async def test_empty_query_empty_image_returns_400(self, client):
        response = await client.post(
            "/api/v1/search",
            json={"query": "", "image": ""},
        )

        assert response.status_code == 400

    async def test_invalid_limit_returns_422(self, client):
        response = await client.post(
            "/api/v1/search",
            json={"query": "셔츠", "limit": 0},
        )

        assert response.status_code == 422

    async def test_limit_exceeds_max_returns_422(self, client):
        response = await client.post(
            "/api/v1/search",
            json={"query": "셔츠", "limit": 101},
        )

        assert response.status_code == 422


class TestSearchCaching:
    async def test_cache_hit_returns_cached_response(
        self, client, mock_cache_service, mock_embedding_service
    ):
        cached_data = {
            "results": [_make_product_result("p001").model_dump()],
            "total": 1,
            "query_type": "text",
        }
        mock_cache_service.get = AsyncMock(return_value=cached_data)

        response = await client.post(
            "/api/v1/search",
            json={"query": "셔츠"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        mock_embedding_service.embed_text.assert_not_awaited()

    async def test_cache_miss_stores_result(
        self, client, mock_cache_service
    ):
        mock_cache_service.get = AsyncMock(return_value=None)

        await client.post(
            "/api/v1/search",
            json={"query": "셔츠"},
        )

        mock_cache_service.set.assert_awaited_once()


class TestSearchEmptyResults:
    async def test_returns_empty_when_no_matches(
        self, client, mock_search_service
    ):
        mock_search_service.search_by_vector = AsyncMock(return_value=[])

        response = await client.post(
            "/api/v1/search",
            json={"query": "존재하지않는검색어"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["results"] == []


class TestSearchServiceFailure:
    async def test_pinecone_failure_returns_503(
        self, client, mock_search_service
    ):
        mock_search_service.search_by_vector = AsyncMock(
            side_effect=ConnectionError("Pinecone unreachable")
        )

        response = await client.post(
            "/api/v1/search",
            json={"query": "셔츠"},
        )

        assert response.status_code == 503
        assert "장애" in response.json()["detail"]

    async def test_supabase_failure_returns_503(
        self, client, mock_search_service
    ):
        mock_search_service.search_by_vector = AsyncMock(
            side_effect=TimeoutError("Supabase timeout")
        )

        response = await client.post(
            "/api/v1/search",
            json={"query": "바지"},
        )

        assert response.status_code == 503
