"""AI 추천 코멘트 엔드포인트.

선택한 상품에 대한 AI 스타일리스트 추천 코멘트를 생성한다.
비스트리밍(JSON) 및 스트리밍(SSE) 모드를 지원한다.
"""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.core.dependencies import get_cache_service, get_recommend_service
from app.models.schemas import (
    ErrorResponse,
    RecommendRequest,
    RecommendResponse,
)
from app.services.cache import CacheService
from app.services.recommend import RecommendService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["recommend"])


def _build_recommend_cache_key(product_ids: list[str], user_query: str | None) -> str:
    """추천 요청용 캐시 키를 생성한다."""
    data = {
        "product_ids": sorted(product_ids),
        "user_query": user_query or "",
    }
    return CacheService.build_cache_key(data).replace("search:", "recommend:", 1)


@router.post(
    "/recommend",
    response_model=RecommendResponse,
    responses={
        400: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
    summary="AI 추천 코멘트",
    description="선택한 상품에 대한 AI 스타일리스트 추천 코멘트를 생성합니다.",
)
async def recommend(
    request: RecommendRequest,
    stream: bool = Query(default=False, description="SSE 스트리밍 모드"),
    recommend_service: RecommendService = Depends(get_recommend_service),
    cache_service: CacheService = Depends(get_cache_service),
) -> RecommendResponse | StreamingResponse:
    if stream:
        return await _recommend_stream(request, recommend_service)

    return await _recommend_json(request, recommend_service, cache_service)


async def _recommend_json(
    request: RecommendRequest,
    recommend_service: RecommendService,
    cache_service: CacheService,
) -> RecommendResponse:
    """비스트리밍 JSON 응답을 반환한다."""
    cache_key = _build_recommend_cache_key(request.product_ids, request.user_query)

    # 캐시 확인
    cached = await cache_service.get(cache_key)
    if cached is not None:
        logger.info("추천 캐시 히트: %s", cache_key)
        return RecommendResponse(**cached)

    try:
        comment = await recommend_service.generate_comment(
            product_ids=request.product_ids,
            user_query=request.user_query,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        logger.error("LLM 호출 실패: %s", exc, exc_info=True)
        raise HTTPException(status_code=503, detail="추천 서비스 일시 장애") from exc

    response = RecommendResponse(
        comment=comment,
        product_ids=request.product_ids,
    )

    # 캐시 저장
    await cache_service.set(cache_key, response.model_dump())
    logger.info("추천 코멘트 생성 완료: product_ids=%s", request.product_ids)

    return response


async def _recommend_stream(
    request: RecommendRequest,
    recommend_service: RecommendService,
) -> StreamingResponse:
    """SSE 스트리밍 응답을 반환한다."""

    async def event_generator():
        try:
            async for chunk in recommend_service.generate_comment_stream(
                product_ids=request.product_ids,
                user_query=request.user_query,
            ):
                event_data = json.dumps(
                    {"event": "delta", "data": chunk},
                    ensure_ascii=False,
                )
                yield f"data: {event_data}\n\n"

            done_data = json.dumps(
                {"event": "done", "data": ""},
                ensure_ascii=False,
            )
            yield f"data: {done_data}\n\n"

        except ValueError as exc:
            error_data = json.dumps(
                {"event": "error", "data": str(exc)},
                ensure_ascii=False,
            )
            yield f"data: {error_data}\n\n"

        except Exception as exc:
            logger.error("스트리밍 생성 실패: %s", exc, exc_info=True)
            error_data = json.dumps(
                {"event": "error", "data": "추천 서비스 일시 장애"},
                ensure_ascii=False,
            )
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
