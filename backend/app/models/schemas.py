from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str


class SearchRequest(BaseModel):
    query: str | None = Field(default=None, description="텍스트 검색 쿼리")
    image: str | None = Field(
        default=None,
        max_length=14_000_000,
        description="Base64 인코딩 이미지 (최대 ~10MB)",
    )
    category: str | None = None
    sub_category: str | None = None
    brand: str | None = None
    min_price: int | None = Field(default=None, ge=0)
    max_price: int | None = Field(default=None, ge=0)
    color: str | None = None
    season: str | None = None
    limit: int = Field(default=20, ge=1, le=100)


class ProductResult(BaseModel):
    product_id: str
    name: str
    name_ko: str | None = None
    price: int
    brand: str | None = None
    category: str | None = None
    sub_category: str | None = None
    style_tags: list[str] = Field(default_factory=list)
    color: str | None = None
    image_url: str
    score: float = Field(ge=0.0, le=1.0)


class SearchResponse(BaseModel):
    results: list[ProductResult]
    total: int
    query_type: Literal["text", "image", "hybrid"]


class RecommendRequest(BaseModel):
    product_ids: list[str] = Field(min_length=1, max_length=10)
    user_query: str | None = None


class RecommendResponse(BaseModel):
    comment: str
    product_ids: list[str]


class ErrorResponse(BaseModel):
    detail: str
