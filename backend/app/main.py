from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import router as v1_router
from app.core.dependencies import get_settings
from app.models.schemas import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Startup: M2~M3에서 CLIP 모델, Redis 연결 초기화 추가 예정
    yield
    # Shutdown: 리소스 정리


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
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router)


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health() -> HealthResponse:
    return HealthResponse(version=settings.app_version)
