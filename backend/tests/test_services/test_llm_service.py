"""LLMService 유닛 테스트."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.llm import LLMService


class TestLLMServiceInit:
    """LLMService 초기화 테스트."""

    def test_init_with_api_key(self) -> None:
        """API 키가 있으면 클라이언트가 초기화된다."""
        with patch.dict("sys.modules", {"openai": MagicMock()}):
            import importlib
            import app.services.llm as llm_module
            importlib.reload(llm_module)

            service = llm_module.LLMService(api_key="test-key", model="gpt-4o-mini")
            assert service._client is not None

    def test_init_without_api_key(self) -> None:
        """API 키가 없으면 클라이언트가 None이다."""
        service = LLMService(api_key="", model="gpt-4o-mini")
        assert service._client is None

    def test_init_stores_config(self) -> None:
        """설정 값이 저장된다."""
        service = LLMService(
            api_key="",
            model="gpt-4o",
            max_tokens=500,
            temperature=0.5,
        )
        assert service._model == "gpt-4o"
        assert service._max_tokens == 500
        assert service._temperature == 0.5


class TestLLMServiceGenerate:
    """LLMService.generate() 테스트."""

    @pytest.fixture
    def mock_client(self) -> MagicMock:
        """목 OpenAI 클라이언트."""
        client = MagicMock()
        response = MagicMock()
        response.choices = [MagicMock()]
        response.choices[0].message.content = "생성된 텍스트"
        client.chat.completions.create.return_value = response
        return client

    @pytest.fixture
    def service(self, mock_client: MagicMock) -> LLMService:
        """테스트용 LLMService."""
        svc = LLMService(api_key="")
        svc._client = mock_client
        return svc

    @pytest.mark.asyncio
    async def test_generate_success(
        self, service: LLMService, mock_client: MagicMock
    ) -> None:
        """정상적으로 텍스트를 생성한다."""
        result = await service.generate("시스템", "사용자")
        assert result == "생성된 텍스트"
        mock_client.chat.completions.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_passes_correct_params(
        self, service: LLMService, mock_client: MagicMock
    ) -> None:
        """올바른 파라미터로 API를 호출한다."""
        await service.generate("시스템 프롬프트", "사용자 메시지")

        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == "gpt-4o-mini"
        assert call_kwargs["messages"][0]["role"] == "system"
        assert call_kwargs["messages"][0]["content"] == "시스템 프롬프트"
        assert call_kwargs["messages"][1]["role"] == "user"
        assert call_kwargs["messages"][1]["content"] == "사용자 메시지"

    @pytest.mark.asyncio
    async def test_generate_without_client_raises(self) -> None:
        """클라이언트 없이 호출하면 RuntimeError가 발생한다."""
        service = LLMService(api_key="")
        with pytest.raises(RuntimeError, match="초기화되지 않았습니다"):
            await service.generate("시스템", "사용자")

    @pytest.mark.asyncio
    async def test_generate_api_error_raises(
        self, service: LLMService, mock_client: MagicMock
    ) -> None:
        """API 오류 시 RuntimeError가 발생한다."""
        mock_client.chat.completions.create.side_effect = Exception("API 오류")
        with pytest.raises(RuntimeError, match="LLM 호출 실패"):
            await service.generate("시스템", "사용자")


class TestLLMServiceGenerateStream:
    """LLMService.generate_stream() 테스트."""

    @pytest.fixture
    def mock_stream_client(self) -> MagicMock:
        """스트리밍 목 클라이언트."""
        client = MagicMock()

        def create_chunks():
            for text in ["안녕", "하세요", "!"]:
                chunk = MagicMock()
                chunk.choices = [MagicMock()]
                chunk.choices[0].delta.content = text
                yield chunk

        client.chat.completions.create.return_value = create_chunks()
        return client

    @pytest.fixture
    def stream_service(self, mock_stream_client: MagicMock) -> LLMService:
        """스트리밍 테스트용 서비스."""
        svc = LLMService(api_key="")
        svc._client = mock_stream_client
        return svc

    @pytest.mark.asyncio
    async def test_generate_stream_yields_chunks(
        self, stream_service: LLMService
    ) -> None:
        """스트리밍 생성이 청크를 순서대로 반환한다."""
        chunks = []
        async for chunk in stream_service.generate_stream("시스템", "사용자"):
            chunks.append(chunk)
        assert chunks == ["안녕", "하세요", "!"]

    @pytest.mark.asyncio
    async def test_generate_stream_without_client_raises(self) -> None:
        """클라이언트 없이 스트리밍하면 RuntimeError가 발생한다."""
        service = LLMService(api_key="")
        with pytest.raises(RuntimeError, match="초기화되지 않았습니다"):
            async for _ in service.generate_stream("시스템", "사용자"):
                pass

    @pytest.mark.asyncio
    async def test_generate_stream_handles_empty_delta(self) -> None:
        """빈 delta는 건너뛴다."""
        client = MagicMock()

        def create_chunks_with_empty():
            for text in ["텍스트", None, "", "완료"]:
                chunk = MagicMock()
                chunk.choices = [MagicMock()]
                chunk.choices[0].delta.content = text
                yield chunk

        client.chat.completions.create.return_value = create_chunks_with_empty()

        service = LLMService(api_key="")
        service._client = client

        chunks = []
        async for chunk in service.generate_stream("시스템", "사용자"):
            chunks.append(chunk)
        assert chunks == ["텍스트", "완료"]

    @pytest.mark.asyncio
    async def test_generate_stream_calls_with_stream_true(
        self, stream_service: LLMService, mock_stream_client: MagicMock
    ) -> None:
        """스트리밍 호출 시 stream=True가 전달된다."""
        chunks = []
        async for chunk in stream_service.generate_stream("시스템", "사용자"):
            chunks.append(chunk)

        call_kwargs = mock_stream_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["stream"] is True
