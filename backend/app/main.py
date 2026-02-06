import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import router as v1_router
from app.core.dependencies import get_settings
from app.models.schemas import HealthResponse
from app.services.embedding import EmbeddingService

logger = logging.getLogger(__name__)

# DEV_MODE: 외부 서비스 없이 Mock으로 실행
DEV_MODE = os.getenv("DEV_MODE", "").lower() in ("1", "true")


MOCK_PRODUCTS = [
    {
        "product_id": "mock_001",
        "name": "Oversized Cotton Shirt",
        "name_ko": "오버사이즈 코튼 셔츠",
        "price": 45000,
        "brand": "MUSINSA STANDARD",
        "category": "상의",
        "sub_category": "셔츠",
        "style_tags": ["캐주얼", "오버핏"],
        "color": "화이트",
        "image_url": "https://picsum.photos/seed/shirt1/400/500",
        "score": 0.95,
    },
    {
        "product_id": "mock_002",
        "name": "Wide Denim Pants",
        "name_ko": "와이드 데님 팬츠",
        "price": 58000,
        "brand": "COVERNAT",
        "category": "하의",
        "sub_category": "데님",
        "style_tags": ["캐주얼", "스트릿"],
        "color": "블루",
        "image_url": "https://picsum.photos/seed/pants1/400/500",
        "score": 0.92,
    },
    {
        "product_id": "mock_003",
        "name": "Minimal Hoodie",
        "name_ko": "미니멀 후드티",
        "price": 39000,
        "brand": "THISISNEVERTHAT",
        "category": "상의",
        "sub_category": "후드",
        "style_tags": ["미니멀", "캐주얼"],
        "color": "블랙",
        "image_url": "https://picsum.photos/seed/hoodie1/400/500",
        "score": 0.91,
    },
    {
        "product_id": "mock_004",
        "name": "Wool Blend Coat",
        "name_ko": "울 블렌드 코트",
        "price": 129000,
        "brand": "HANCOSTORE",
        "category": "아우터",
        "sub_category": "코트",
        "style_tags": ["미니멀", "클래식"],
        "color": "베이지",
        "image_url": "https://picsum.photos/seed/coat1/400/500",
        "score": 0.89,
    },
    {
        "product_id": "mock_005",
        "name": "Stripe T-Shirt",
        "name_ko": "스트라이프 티셔츠",
        "price": 29000,
        "brand": "MUSINSA STANDARD",
        "category": "상의",
        "sub_category": "티셔츠",
        "style_tags": ["캐주얼", "레트로"],
        "color": "네이비",
        "image_url": "https://picsum.photos/seed/tshirt1/400/500",
        "score": 0.88,
    },
    {
        "product_id": "mock_006",
        "name": "Chino Pants",
        "name_ko": "치노 팬츠",
        "price": 45000,
        "brand": "COVERNAT",
        "category": "하의",
        "sub_category": "슬랙스",
        "style_tags": ["캐주얼", "클래식"],
        "color": "카키",
        "image_url": "https://picsum.photos/seed/chino1/400/500",
        "score": 0.87,
    },
    {
        "product_id": "mock_007",
        "name": "Knit Cardigan",
        "name_ko": "니트 가디건",
        "price": 55000,
        "brand": "HANCOSTORE",
        "category": "상의",
        "sub_category": "니트",
        "style_tags": ["레트로", "로맨틱"],
        "color": "아이보리",
        "image_url": "https://picsum.photos/seed/cardigan1/400/500",
        "score": 0.85,
    },
    {
        "product_id": "mock_008",
        "name": "MA-1 Jacket",
        "name_ko": "MA-1 자켓",
        "price": 89000,
        "brand": "THISISNEVERTHAT",
        "category": "아우터",
        "sub_category": "자켓",
        "style_tags": ["스트릿", "밀리터리"],
        "color": "블랙",
        "image_url": "https://picsum.photos/seed/ma1/400/500",
        "score": 0.84,
    },
]


def _create_mock_services(app: FastAPI) -> None:
    """개발용 Mock 서비스 생성."""
    logger.warning("DEV_MODE 활성화 - Mock 서비스 사용")

    # Mock EmbeddingService
    app.state.embedding_service = EmbeddingService(device="cpu")

    # Mock SearchService - 샘플 데이터 반환
    mock_search = MagicMock()
    mock_search.search_by_vector = AsyncMock(return_value=MOCK_PRODUCTS)
    app.state.search_service = mock_search

    # Mock CacheService
    mock_cache = MagicMock()
    mock_cache.get = AsyncMock(return_value=None)
    mock_cache.set = AsyncMock(return_value=None)
    mock_cache.close = AsyncMock()
    app.state.cache_service = mock_cache

    # Mock RecommendService
    mock_recommend = MagicMock()
    mock_recommend.generate_comment = AsyncMock(
        return_value="[DEV MODE] 이 상품은 캐주얼한 스타일로 데일리룩에 적합합니다. 편안하면서도 트렌디한 무드를 연출할 수 있어요."
    )

    async def mock_stream(*args, **kwargs):
        chunks = [
            "[DEV MODE] ",
            "이 상품은 ",
            "캐주얼한 스타일로 ",
            "데일리룩에 적합합니다. ",
            "편안하면서도 ",
            "트렌디한 무드를 ",
            "연출할 수 있어요.",
        ]
        for chunk in chunks:
            yield chunk

    mock_recommend.generate_comment_stream = mock_stream
    app.state.recommend_service = mock_recommend


async def _create_real_services(app: FastAPI) -> None:
    """실제 외부 서비스 연결."""
    import redis.asyncio as aioredis
    from pinecone import Pinecone
    from supabase import create_client

    from app.services.cache import CacheService
    from app.services.llm import LLMService
    from app.services.recommend import RecommendService
    from app.services.search import SearchService

    settings = get_settings()

    # CLIP EmbeddingService
    device = settings.clip_device or None
    embedding_service = EmbeddingService(device=device)
    app.state.embedding_service = embedding_service
    logger.info("EmbeddingService 초기화 완료")

    # Pinecone Index + Supabase → SearchService
    pc = Pinecone(api_key=settings.pinecone_api_key)
    pinecone_index = pc.Index(settings.pinecone_index)
    logger.info("Pinecone 인덱스 연결: %s", settings.pinecone_index)

    supabase_client = create_client(
        settings.supabase_url, settings.supabase_service_key
    )
    logger.info("Supabase 클라이언트 초기화 완료")

    search_service = SearchService(
        pinecone_index=pinecone_index,
        supabase_client=supabase_client,
    )
    app.state.search_service = search_service
    logger.info("SearchService 초기화 완료")

    # Redis → CacheService
    redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    cache_service = CacheService(redis_client=redis_client)
    app.state.cache_service = cache_service
    logger.info("CacheService 초기화 완료")

    # LLM + RecommendService
    llm_service = LLMService(
        api_key=settings.openai_api_key,
        model=settings.llm_model,
        max_tokens=settings.llm_max_tokens,
        temperature=settings.llm_temperature,
    )
    recommend_service = RecommendService(
        llm_service=llm_service,
        supabase_client=supabase_client,
    )
    app.state.recommend_service = recommend_service
    logger.info("RecommendService 초기화 완료")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    if DEV_MODE:
        _create_mock_services(app)
    else:
        await _create_real_services(app)

    yield

    # Shutdown
    if hasattr(app.state, "cache_service"):
        await app.state.cache_service.close()
    logger.info("리소스 정리 완료")


settings = get_settings()

app = FastAPI(
    title="Style Matcher API",
    description="이미지와 자연어를 결합한 멀티모달 AI 패션 검색 서비스",
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(v1_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("처리되지 않은 오류 발생")
    return JSONResponse(
        status_code=500,
        content={"detail": "서버 내부 오류가 발생했습니다"},
    )


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health() -> HealthResponse:
    return HealthResponse(version=settings.app_version)
