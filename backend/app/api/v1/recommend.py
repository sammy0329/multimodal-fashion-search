from fastapi import APIRouter, HTTPException

from app.models.schemas import ErrorResponse, RecommendRequest, RecommendResponse

router = APIRouter(tags=["recommend"])


@router.post(
    "/recommend",
    response_model=RecommendResponse,
    responses={501: {"model": ErrorResponse}},
    summary="AI 추천 코멘트",
    description="선택한 상품에 대한 AI 스타일리스트 추천 코멘트를 생성합니다.",
)
async def recommend(request: RecommendRequest) -> RecommendResponse:
    raise HTTPException(status_code=501, detail="M4에서 구현 예정")
