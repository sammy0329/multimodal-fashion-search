from fastapi import APIRouter, HTTPException

from app.models.schemas import ErrorResponse, SearchRequest, SearchResponse

router = APIRouter(tags=["search"])


@router.post(
    "/search",
    response_model=SearchResponse,
    responses={501: {"model": ErrorResponse}},
    summary="멀티모달 검색",
    description="이미지, 텍스트, 또는 복합 입력으로 패션 상품을 검색합니다.",
)
async def search(request: SearchRequest) -> SearchResponse:
    raise HTTPException(status_code=501, detail="M3에서 구현 예정")
