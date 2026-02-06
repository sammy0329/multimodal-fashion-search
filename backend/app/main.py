import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pinecone import Pinecone
from supabase import create_client

from app.api.v1 import router as v1_router
from app.core.dependencies import get_settings
from app.models.schemas import HealthResponse
from app.services.cache import CacheService
from app.services.embedding import EmbeddingService
from app.services.llm import LLMService
from app.services.recommend import RecommendService
from app.services.search import SearchService

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
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

    yield

    # Shutdown
    await cache_service.close()
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
