class SearchService:
    """Pinecone 벡터 검색 서비스. M3에서 구현 예정."""

    async def search_by_vector(
        self,
        vector: list[float],
        top_k: int = 20,
        filters: dict | None = None,
    ) -> list[dict]:
        """벡터 유사도 기반 상품 검색."""
        raise NotImplementedError("M3에서 구현 예정")
