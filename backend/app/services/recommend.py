"""LLM 기반 추천 코멘트 생성 서비스.

상품 정보를 조회하고 LLM으로 AI 스타일리스트 코멘트를 생성한다.
"""

import asyncio
import logging
from collections.abc import AsyncIterator
from functools import partial
from typing import Any

from supabase import Client as SupabaseClient

from app.services.llm import LLMService
from app.services.prompt import SYSTEM_PROMPT, build_product_context, build_user_message

logger = logging.getLogger(__name__)

PRODUCT_COLUMNS = (
    "product_id,name,name_ko,price,brand,category,"
    "sub_category,style_tags,color,material,season,description"
)


class RecommendService:
    """LLM 기반 추천 코멘트 생성 서비스.

    Args:
        llm_service: LLM API 클라이언트.
        supabase_client: Supabase Client 인스턴스.
    """

    def __init__(
        self,
        llm_service: LLMService,
        supabase_client: SupabaseClient,
    ) -> None:
        self._llm = llm_service
        self._supabase = supabase_client

    def _fetch_products_sync(self, product_ids: list[str]) -> list[dict[str, Any]]:
        """Supabase에서 상품 상세 정보를 조회한다 (동기).

        Args:
            product_ids: 조회할 상품 ID 리스트.

        Returns:
            상품 딕셔너리 리스트 (입력 순서 유지).
        """
        if not product_ids:
            return []

        response = (
            self._supabase.table("products")
            .select(PRODUCT_COLUMNS)
            .in_("product_id", product_ids)
            .execute()
        )

        products_map = {row["product_id"]: row for row in response.data}
        return [products_map[pid] for pid in product_ids if pid in products_map]

    async def _get_products(self, product_ids: list[str]) -> list[dict[str, Any]]:
        """상품 정보를 비동기로 조회한다."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            partial(self._fetch_products_sync, product_ids),
        )

    async def generate_comment(
        self,
        product_ids: list[str],
        user_query: str | None = None,
    ) -> str:
        """상품 목록에 대한 AI 추천 코멘트를 생성한다.

        Args:
            product_ids: 추천할 상품 ID 리스트 (1~10개).
            user_query: 원래 검색 쿼리 (선택).

        Returns:
            AI 생성 추천 코멘트.

        Raises:
            ValueError: 상품을 찾을 수 없을 때.
            RuntimeError: LLM 호출 실패 시.
        """
        products = await self._get_products(product_ids)
        if not products:
            raise ValueError("요청한 상품을 찾을 수 없습니다")

        product_context = build_product_context(products)
        user_message = build_user_message(product_context, user_query)

        logger.info(
            "추천 코멘트 생성 시작: product_ids=%s, user_query=%s",
            product_ids,
            user_query,
        )
        return await self._llm.generate(SYSTEM_PROMPT, user_message)

    async def generate_comment_stream(
        self,
        product_ids: list[str],
        user_query: str | None = None,
    ) -> AsyncIterator[str]:
        """상품 목록에 대한 AI 추천 코멘트를 스트리밍 생성한다.

        Args:
            product_ids: 추천할 상품 ID 리스트.
            user_query: 원래 검색 쿼리 (선택).

        Yields:
            텍스트 청크.

        Raises:
            ValueError: 상품을 찾을 수 없을 때.
        """
        products = await self._get_products(product_ids)
        if not products:
            raise ValueError("요청한 상품을 찾을 수 없습니다")

        product_context = build_product_context(products)
        user_message = build_user_message(product_context, user_query)

        logger.info(
            "추천 코멘트 스트리밍 시작: product_ids=%s, user_query=%s",
            product_ids,
            user_query,
        )
        async for chunk in self._llm.generate_stream(SYSTEM_PROMPT, user_message):
            yield chunk
