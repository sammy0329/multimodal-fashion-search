"""SearchService 유닛 테스트.

Pinecone, Supabase를 mock하여 검색 로직만 검증한다.
"""

from unittest.mock import MagicMock

import pytest

from app.models.schemas import ProductResult
from app.services.search import SearchService


def _make_pinecone_response(matches: list[dict]) -> dict:
    """Pinecone 응답 형식의 dict를 만든다."""
    return {"matches": matches}


def _make_pinecone_match(
    product_id: str, score: float, metadata: dict | None = None
) -> dict:
    return {
        "id": f"product_{product_id}",
        "score": score,
        "metadata": metadata or {},
    }


def _make_supabase_product(product_id: str, **kwargs) -> dict:
    defaults = {
        "product_id": product_id,
        "name": f"Product {product_id}",
        "name_ko": f"상품 {product_id}",
        "price": 50000,
        "brand": "test_brand",
        "category": "상의",
        "sub_category": "셔츠",
        "style_tags": ["캐주얼"],
        "color": "화이트",
        "image_url": f"https://example.com/{product_id}.jpg",
    }
    return {**defaults, **kwargs}


@pytest.fixture
def mock_pinecone_index():
    return MagicMock()


@pytest.fixture
def mock_supabase_client():
    return MagicMock()


@pytest.fixture
def search_service(mock_pinecone_index, mock_supabase_client):
    return SearchService(
        pinecone_index=mock_pinecone_index,
        supabase_client=mock_supabase_client,
    )


class TestQueryPineconeSync:
    def test_extracts_product_ids_from_matches(
        self, search_service, mock_pinecone_index
    ):
        mock_pinecone_index.query.return_value = _make_pinecone_response([
            _make_pinecone_match("p001", 0.95),
            _make_pinecone_match("p002", 0.88),
        ])

        results = search_service._query_pinecone_sync([0.1] * 512, 10, None)

        assert len(results) == 2
        assert results[0]["product_id"] == "p001"
        assert results[0]["score"] == 0.95
        assert results[1]["product_id"] == "p002"

    def test_passes_filters_to_query(self, search_service, mock_pinecone_index):
        mock_pinecone_index.query.return_value = _make_pinecone_response([])
        filters = {"category": {"$eq": "상의"}}

        search_service._query_pinecone_sync([0.1] * 512, 5, filters)

        call_kwargs = mock_pinecone_index.query.call_args.kwargs
        assert call_kwargs["filter"] == filters

    def test_returns_empty_on_no_matches(self, search_service, mock_pinecone_index):
        mock_pinecone_index.query.return_value = _make_pinecone_response([])

        results = search_service._query_pinecone_sync([0.1] * 512, 10, None)

        assert results == []


class TestFetchProductsSync:
    def test_returns_product_map(self, search_service, mock_supabase_client):
        mock_response = MagicMock()
        mock_response.data = [
            _make_supabase_product("p001"),
            _make_supabase_product("p002"),
        ]
        (
            mock_supabase_client.table.return_value
            .select.return_value
            .in_.return_value
            .execute.return_value
        ) = mock_response

        result = search_service._fetch_products_sync(["p001", "p002"])

        assert "p001" in result
        assert "p002" in result
        assert result["p001"]["name"] == "Product p001"

    def test_returns_empty_for_no_ids(self, search_service):
        result = search_service._fetch_products_sync([])

        assert result == {}


class TestSearchByVector:
    async def test_returns_product_results(
        self, search_service, mock_pinecone_index, mock_supabase_client
    ):
        mock_pinecone_index.query.return_value = _make_pinecone_response([
            _make_pinecone_match("p001", 0.95),
        ])

        mock_response = MagicMock()
        mock_response.data = [_make_supabase_product("p001")]
        (
            mock_supabase_client.table.return_value
            .select.return_value
            .in_.return_value
            .execute.return_value
        ) = mock_response

        results = await search_service.search_by_vector([0.1] * 512, top_k=5)

        assert len(results) == 1
        assert isinstance(results[0], ProductResult)
        assert results[0].product_id == "p001"
        assert results[0].score == 0.95
        assert results[0].name == "Product p001"

    async def test_returns_empty_on_no_matches(
        self, search_service, mock_pinecone_index
    ):
        mock_pinecone_index.query.return_value = _make_pinecone_response([])

        results = await search_service.search_by_vector([0.1] * 512)

        assert results == []

    async def test_falls_back_to_metadata_when_supabase_missing(
        self, search_service, mock_pinecone_index, mock_supabase_client
    ):
        mock_pinecone_index.query.return_value = _make_pinecone_response([
            _make_pinecone_match("p999", 0.80, {"category": "하의", "price": 30000}),
        ])

        mock_response = MagicMock()
        mock_response.data = []
        (
            mock_supabase_client.table.return_value
            .select.return_value
            .in_.return_value
            .execute.return_value
        ) = mock_response

        results = await search_service.search_by_vector([0.1] * 512)

        assert len(results) == 1
        assert results[0].product_id == "p999"
        assert results[0].name == "하의"
        assert results[0].price == 30000


class TestMergeResults:
    def test_merges_with_full_product_data(self):
        pinecone_results = [
            {"product_id": "p001", "score": 0.95, "metadata": {}},
        ]
        products_map = {"p001": _make_supabase_product("p001")}

        merged = SearchService._merge_results(pinecone_results, products_map)

        assert len(merged) == 1
        assert merged[0].brand == "test_brand"
        assert merged[0].style_tags == ["캐주얼"]

    def test_handles_missing_product(self):
        pinecone_results = [
            {
                "product_id": "p999",
                "score": 0.70,
                "metadata": {"category": "하의"},
            },
        ]

        merged = SearchService._merge_results(pinecone_results, {})

        assert len(merged) == 1
        assert merged[0].name == "하의"

    def test_preserves_order(self):
        pinecone_results = [
            {"product_id": "p001", "score": 0.95, "metadata": {}},
            {"product_id": "p002", "score": 0.88, "metadata": {}},
            {"product_id": "p003", "score": 0.75, "metadata": {}},
        ]
        products_map = {
            pid: _make_supabase_product(pid) for pid in ["p001", "p002", "p003"]
        }

        merged = SearchService._merge_results(pinecone_results, products_map)

        assert [r.product_id for r in merged] == ["p001", "p002", "p003"]


class TestBuildFilters:
    def test_always_includes_soldout_filter(self):
        filters = SearchService.build_filters()

        assert filters["is_soldout"] == {"$eq": False}

    def test_category_filter(self):
        filters = SearchService.build_filters(category="상의")

        assert filters["category"] == {"$eq": "상의"}

    def test_price_range_filter(self):
        filters = SearchService.build_filters(min_price=10000, max_price=50000)

        assert filters["price"] == {"$gte": 10000, "$lte": 50000}

    def test_min_price_only(self):
        filters = SearchService.build_filters(min_price=20000)

        assert filters["price"] == {"$gte": 20000}

    def test_max_price_only(self):
        filters = SearchService.build_filters(max_price=80000)

        assert filters["price"] == {"$lte": 80000}

    def test_all_filters(self):
        filters = SearchService.build_filters(
            category="상의",
            sub_category="셔츠",
            brand="brand_a",
            min_price=10000,
            max_price=50000,
            color="화이트",
            season="여름",
        )

        assert filters["category"] == {"$eq": "상의"}
        assert filters["sub_category"] == {"$eq": "셔츠"}
        assert filters["brand"] == {"$eq": "brand_a"}
        assert filters["color"] == {"$eq": "화이트"}
        assert filters["season"] == {"$eq": "여름"}
        assert filters["price"] == {"$gte": 10000, "$lte": 50000}
        assert filters["is_soldout"] == {"$eq": False}

    def test_no_optional_filters(self):
        filters = SearchService.build_filters()

        assert len(filters) == 1
        assert "is_soldout" in filters
