"""Pinecone 벡터 검색 + Supabase 메타데이터 보강 서비스.

벡터 유사도 검색 결과에 Supabase의 상품 상세 정보를 병합한다.
"""

import asyncio
import logging
from functools import partial
from typing import Any

from pinecone import Index as PineconeIndex
from supabase import Client as SupabaseClient

from app.models.schemas import ProductResult

logger = logging.getLogger(__name__)


class SearchService:
    """Pinecone 벡터 검색 + Supabase 보강 서비스.

    Args:
        pinecone_index: Pinecone Index 인스턴스.
        supabase_client: Supabase Client 인스턴스.
    """

    def __init__(
        self,
        pinecone_index: PineconeIndex,
        supabase_client: SupabaseClient,
    ) -> None:
        self._index = pinecone_index
        self._supabase = supabase_client

    def _query_pinecone_sync(
        self,
        vector: list[float],
        top_k: int,
        filters: dict[str, Any] | None,
    ) -> list[dict]:
        """Pinecone 벡터 검색을 실행한다 (동기).

        Returns:
            [{"product_id": str, "score": float}, ...]
        """
        query_params: dict[str, Any] = {
            "vector": vector,
            "top_k": top_k,
            "include_metadata": True,
        }
        if filters:
            query_params["filter"] = filters

        response = self._index.query(**query_params)

        results = []
        for match in response.get("matches", []):
            vec_id: str = match["id"]
            product_id = vec_id.removeprefix("product_")
            results.append(
                {
                    "product_id": product_id,
                    "score": float(match["score"]),
                    "metadata": match.get("metadata", {}),
                }
            )

        return results

    def _fetch_products_sync(self, product_ids: list[str]) -> dict[str, dict]:
        """Supabase에서 상품 정보를 배치 조회한다 (동기).

        Returns:
            {product_id: 상품 딕셔너리} 매핑.
        """
        if not product_ids:
            return {}

        response = (
            self._supabase.table("products")
            .select(
                "product_id,name,name_ko,price,brand,"
                "category,sub_category,style_tags,color,image_url"
            )
            .in_("product_id", product_ids)
            .execute()
        )

        return {row["product_id"]: row for row in response.data}

    async def search_by_vector(
        self,
        vector: list[float],
        top_k: int = 20,
        filters: dict[str, Any] | None = None,
    ) -> list[ProductResult]:
        """벡터 유사도 기반 상품 검색.

        1) Pinecone 벡터 검색
        2) Supabase 상품 정보 보강
        3) 점수 기준 정렬

        Args:
            vector: 512차원 검색 벡터.
            top_k: 반환할 최대 결과 수.
            filters: Pinecone 메타데이터 필터.

        Returns:
            ProductResult 리스트 (점수 내림차순).
        """
        loop = asyncio.get_running_loop()

        pinecone_results = await loop.run_in_executor(
            None,
            partial(self._query_pinecone_sync, vector, top_k, filters),
        )

        if not pinecone_results:
            return []

        product_ids = [r["product_id"] for r in pinecone_results]

        products_map = await loop.run_in_executor(
            None,
            partial(self._fetch_products_sync, product_ids),
        )

        return self._merge_results(pinecone_results, products_map)

    @staticmethod
    def _merge_results(
        pinecone_results: list[dict],
        products_map: dict[str, dict],
    ) -> list[ProductResult]:
        """Pinecone 결과와 Supabase 상품 정보를 병합한다."""
        merged = []

        for pc_result in pinecone_results:
            product_id = pc_result["product_id"]
            product = products_map.get(product_id)

            if product is None:
                metadata = pc_result.get("metadata", {})
                merged.append(
                    ProductResult(
                        product_id=product_id,
                        name=metadata.get("category", "Unknown"),
                        price=metadata.get("price", 0),
                        image_url="",
                        score=pc_result["score"],
                    )
                )
                continue

            merged.append(
                ProductResult(
                    product_id=product_id,
                    name=product.get("name", ""),
                    name_ko=product.get("name_ko"),
                    price=product.get("price", 0),
                    brand=product.get("brand"),
                    category=product.get("category"),
                    sub_category=product.get("sub_category"),
                    style_tags=product.get("style_tags") or [],
                    color=product.get("color"),
                    image_url=product.get("image_url", ""),
                    score=pc_result["score"],
                )
            )

        return merged

    @staticmethod
    def build_filters(
        category: str | None = None,
        sub_category: str | None = None,
        brand: str | None = None,
        min_price: int | None = None,
        max_price: int | None = None,
        color: str | None = None,
        season: str | None = None,
    ) -> dict[str, Any]:
        """검색 필터를 Pinecone filter dict로 변환한다.

        항상 is_soldout=False 필터를 포함한다.

        Returns:
            Pinecone 필터 딕셔너리.
        """
        filters: dict[str, Any] = {
            "is_soldout": {"$eq": False},
        }

        if category:
            filters["category"] = {"$eq": category}
        if sub_category:
            filters["sub_category"] = {"$eq": sub_category}
        if brand:
            filters["brand"] = {"$eq": brand}
        if color:
            filters["color"] = {"$eq": color}
        if season:
            filters["season"] = {"$eq": season}

        if min_price is not None or max_price is not None:
            price_filter: dict[str, int] = {}
            if min_price is not None:
                price_filter["$gte"] = min_price
            if max_price is not None:
                price_filter["$lte"] = max_price
            filters["price"] = price_filter

        return filters
