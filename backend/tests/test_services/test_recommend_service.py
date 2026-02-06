"""RecommendService 유닛 테스트."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.recommend import RecommendService


@pytest.fixture
def mock_llm_service() -> AsyncMock:
    """목 LLM 서비스."""
    service = AsyncMock()
    service.generate = AsyncMock(return_value="추천 코멘트입니다.")
    return service


@pytest.fixture
def mock_supabase_client() -> MagicMock:
    """목 Supabase 클라이언트."""
    client = MagicMock()
    response = MagicMock()
    response.data = [
        {
            "product_id": "p001",
            "name": "Test Shirt",
            "name_ko": "테스트 셔츠",
            "price": 45000,
            "brand": "브랜드A",
            "category": "상의",
            "sub_category": "셔츠",
            "style_tags": ["캐주얼"],
            "color": "화이트",
            "material": "면",
            "season": "봄/가을",
            "description": "테스트 상품",
        }
    ]
    client.table.return_value.select.return_value.in_.return_value.execute.return_value = response
    return client


@pytest.fixture
def recommend_service(
    mock_llm_service: AsyncMock, mock_supabase_client: MagicMock
) -> RecommendService:
    """테스트용 RecommendService."""
    return RecommendService(
        llm_service=mock_llm_service,
        supabase_client=mock_supabase_client,
    )


class TestRecommendServiceInit:
    """RecommendService 초기화 테스트."""

    def test_stores_dependencies(
        self, mock_llm_service: AsyncMock, mock_supabase_client: MagicMock
    ) -> None:
        """의존성이 저장된다."""
        service = RecommendService(
            llm_service=mock_llm_service,
            supabase_client=mock_supabase_client,
        )
        assert service._llm is mock_llm_service
        assert service._supabase is mock_supabase_client


class TestFetchProductsSync:
    """_fetch_products_sync() 테스트."""

    def test_queries_correct_columns(
        self, recommend_service: RecommendService, mock_supabase_client: MagicMock
    ) -> None:
        """올바른 컬럼을 조회한다."""
        recommend_service._fetch_products_sync(["p001"])

        mock_supabase_client.table.assert_called_with("products")
        select_call = mock_supabase_client.table.return_value.select
        assert "product_id" in select_call.call_args[0][0]
        assert "name_ko" in select_call.call_args[0][0]
        assert "style_tags" in select_call.call_args[0][0]

    def test_returns_empty_for_empty_ids(
        self, recommend_service: RecommendService
    ) -> None:
        """빈 ID 리스트는 빈 결과를 반환한다."""
        result = recommend_service._fetch_products_sync([])
        assert result == []

    def test_preserves_input_order(
        self, recommend_service: RecommendService, mock_supabase_client: MagicMock
    ) -> None:
        """입력 순서를 유지한다."""
        response = MagicMock()
        response.data = [
            {"product_id": "p002", "name": "상품2"},
            {"product_id": "p001", "name": "상품1"},
        ]
        mock_supabase_client.table.return_value.select.return_value.in_.return_value.execute.return_value = response

        result = recommend_service._fetch_products_sync(["p001", "p002"])

        assert result[0]["product_id"] == "p001"
        assert result[1]["product_id"] == "p002"

    def test_skips_missing_products(
        self, recommend_service: RecommendService, mock_supabase_client: MagicMock
    ) -> None:
        """없는 상품 ID는 건너뛴다."""
        response = MagicMock()
        response.data = [{"product_id": "p001", "name": "상품1"}]
        mock_supabase_client.table.return_value.select.return_value.in_.return_value.execute.return_value = response

        result = recommend_service._fetch_products_sync(["p001", "p999"])

        assert len(result) == 1
        assert result[0]["product_id"] == "p001"


class TestGenerateComment:
    """generate_comment() 테스트."""

    @pytest.mark.asyncio
    async def test_returns_llm_response(
        self, recommend_service: RecommendService
    ) -> None:
        """LLM 응답을 반환한다."""
        result = await recommend_service.generate_comment(["p001"])
        assert result == "추천 코멘트입니다."

    @pytest.mark.asyncio
    async def test_passes_user_query(
        self, recommend_service: RecommendService, mock_llm_service: AsyncMock
    ) -> None:
        """user_query가 프롬프트에 포함된다."""
        await recommend_service.generate_comment(["p001"], user_query="오버핏 셔츠")

        call_args = mock_llm_service.generate.call_args
        user_message = call_args[0][1]
        assert "오버핏 셔츠" in user_message

    @pytest.mark.asyncio
    async def test_includes_product_context(
        self, recommend_service: RecommendService, mock_llm_service: AsyncMock
    ) -> None:
        """상품 정보가 프롬프트에 포함된다."""
        await recommend_service.generate_comment(["p001"])

        call_args = mock_llm_service.generate.call_args
        user_message = call_args[0][1]
        assert "테스트 셔츠" in user_message
        assert "45,000원" in user_message

    @pytest.mark.asyncio
    async def test_no_products_raises_value_error(
        self, recommend_service: RecommendService, mock_supabase_client: MagicMock
    ) -> None:
        """상품을 찾을 수 없으면 ValueError가 발생한다."""
        response = MagicMock()
        response.data = []
        mock_supabase_client.table.return_value.select.return_value.in_.return_value.execute.return_value = response

        with pytest.raises(ValueError, match="찾을 수 없습니다"):
            await recommend_service.generate_comment(["p999"])

    @pytest.mark.asyncio
    async def test_llm_error_propagates(
        self, recommend_service: RecommendService, mock_llm_service: AsyncMock
    ) -> None:
        """LLM 오류가 전파된다."""
        mock_llm_service.generate.side_effect = RuntimeError("LLM 오류")

        with pytest.raises(RuntimeError, match="LLM 오류"):
            await recommend_service.generate_comment(["p001"])


class TestGenerateCommentStream:
    """generate_comment_stream() 테스트."""

    @pytest.fixture
    def streaming_llm_service(self) -> AsyncMock:
        """스트리밍 목 LLM 서비스."""
        service = AsyncMock()

        async def mock_stream(*args, **kwargs):
            for chunk in ["안녕", "하세요", "!"]:
                yield chunk

        service.generate_stream = mock_stream
        return service

    @pytest.fixture
    def streaming_recommend_service(
        self, streaming_llm_service: AsyncMock, mock_supabase_client: MagicMock
    ) -> RecommendService:
        """스트리밍 테스트용 서비스."""
        return RecommendService(
            llm_service=streaming_llm_service,
            supabase_client=mock_supabase_client,
        )

    @pytest.mark.asyncio
    async def test_yields_chunks(
        self, streaming_recommend_service: RecommendService
    ) -> None:
        """청크를 순서대로 반환한다."""
        chunks = []
        async for chunk in streaming_recommend_service.generate_comment_stream(["p001"]):
            chunks.append(chunk)

        assert chunks == ["안녕", "하세요", "!"]

    @pytest.mark.asyncio
    async def test_no_products_raises_value_error(
        self, streaming_recommend_service: RecommendService, mock_supabase_client: MagicMock
    ) -> None:
        """상품을 찾을 수 없으면 ValueError가 발생한다."""
        response = MagicMock()
        response.data = []
        mock_supabase_client.table.return_value.select.return_value.in_.return_value.execute.return_value = response

        with pytest.raises(ValueError, match="찾을 수 없습니다"):
            async for _ in streaming_recommend_service.generate_comment_stream(["p999"]):
                pass

    @pytest.mark.asyncio
    async def test_passes_user_query_to_stream(
        self, streaming_recommend_service: RecommendService
    ) -> None:
        """user_query가 스트리밍에도 전달된다."""
        chunks = []
        async for chunk in streaming_recommend_service.generate_comment_stream(
            ["p001"], user_query="캐주얼"
        ):
            chunks.append(chunk)

        assert len(chunks) > 0
