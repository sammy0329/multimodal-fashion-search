"""멀티모달 검색 엔드포인트.

이미지, 텍스트, 또는 복합 입력으로 패션 상품을 검색한다.
"""

import asyncio
import base64
import hashlib
import logging

from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import (
    get_cache_service,
    get_embedding_service,
    get_search_service,
)
from app.models.schemas import ErrorResponse, SearchRequest, SearchResponse
from app.services.cache import CacheService
from app.services.embedding import EmbeddingService
from app.services.search import SearchService
from app.utils.image import preprocess_image

logger = logging.getLogger(__name__)

router = APIRouter(tags=["search"])


def _determine_query_type(request: SearchRequest) -> str:
    """검색 모드를 판별한다."""
    has_text = request.query is not None and request.query.strip() != ""
    has_image = request.image is not None and request.image.strip() != ""

    if has_text and has_image:
        return "hybrid"
    if has_image:
        return "image"
    if has_text:
        return "text"

    raise HTTPException(
        status_code=400,
        detail="query 또는 image 중 하나 이상 필요합니다",
    )


def _decode_base64_image(image_b64: str) -> bytes:
    """Base64 이미지 문자열을 바이트로 디코딩한다."""
    try:
        return base64.b64decode(image_b64)
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail="유효하지 않은 Base64 이미지입니다",
        ) from exc


@router.post(
    "/search",
    response_model=SearchResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="멀티모달 검색",
    description="이미지, 텍스트, 또는 복합 입력으로 패션 상품을 검색합니다.",
)
async def search(
    request: SearchRequest,
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    search_service: SearchService = Depends(get_search_service),
    cache_service: CacheService = Depends(get_cache_service),
) -> SearchResponse:
    query_type = _determine_query_type(request)

    # 캐시 확인 (이미지 원본 대신 해시 사용)
    cache_key_data = request.model_dump(exclude={"image"})
    if query_type in ("image", "hybrid") and request.image:
        cache_key_data["_image_hash"] = hashlib.sha256(
            request.image.encode()
        ).hexdigest()[:16]

    cache_key = CacheService.build_cache_key(cache_key_data)
    cached = await cache_service.get(cache_key)
    if cached is not None:
        logger.info("캐시 히트: %s", cache_key)
        return SearchResponse(**cached)

    # 임베딩 생성
    try:
        vector = await _build_embedding(query_type, request, embedding_service)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # 필터 구성
    filters = SearchService.build_filters(
        category=request.category,
        sub_category=request.sub_category,
        brand=request.brand,
        min_price=request.min_price,
        max_price=request.max_price,
        color=request.color,
        season=request.season,
    )

    # 벡터 검색
    results = await search_service.search_by_vector(
        vector=vector,
        top_k=request.limit,
        filters=filters,
    )

    response = SearchResponse(
        results=results,
        total=len(results),
        query_type=query_type,
    )

    # 캐시 저장
    await cache_service.set(cache_key, response.model_dump())
    logger.info("검색 완료: type=%s, results=%d", query_type, len(results))

    return response


async def _build_embedding(
    query_type: str,
    request: SearchRequest,
    embedding_service: EmbeddingService,
) -> list[float]:
    """검색 타입에 따라 임베딩 벡터를 생성한다."""
    if query_type == "text":
        assert request.query is not None
        return await embedding_service.embed_text(request.query)

    if query_type == "image":
        assert request.image is not None
        image_bytes = _decode_base64_image(request.image)
        image = preprocess_image(image_bytes)
        return await embedding_service.embed_image(image)

    # hybrid
    assert request.image is not None
    assert request.query is not None
    image_bytes = _decode_base64_image(request.image)
    image = preprocess_image(image_bytes)

    image_embedding, text_embedding = await asyncio.gather(
        embedding_service.embed_image(image),
        embedding_service.embed_text(request.query),
    )

    return EmbeddingService.combine_embeddings(image_embedding, text_embedding)
