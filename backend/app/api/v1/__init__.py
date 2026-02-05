from fastapi import APIRouter

from app.api.v1.recommend import router as recommend_router
from app.api.v1.search import router as search_router

router = APIRouter(prefix="/api/v1")
router.include_router(search_router)
router.include_router(recommend_router)
