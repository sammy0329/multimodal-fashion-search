class RecommendService:
    """LLM 기반 추천 코멘트 생성 서비스. M4에서 구현 예정."""

    async def generate_comment(
        self,
        product_ids: list[str],
        user_query: str | None = None,
    ) -> str:
        """상품 목록에 대한 AI 추천 코멘트 생성."""
        raise NotImplementedError("M4에서 구현 예정")
