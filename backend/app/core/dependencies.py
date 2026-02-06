from functools import lru_cache

from fastapi import Request

from app.core.config import Settings
from app.services.cache import CacheService
from app.services.embedding import EmbeddingService
from app.services.recommend import RecommendService
from app.services.search import SearchService


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_embedding_service(request: Request) -> EmbeddingService:
    return request.app.state.embedding_service


def get_search_service(request: Request) -> SearchService:
    return request.app.state.search_service


def get_cache_service(request: Request) -> CacheService:
    return request.app.state.cache_service


def get_recommend_service(request: Request) -> RecommendService:
    return request.app.state.recommend_service
