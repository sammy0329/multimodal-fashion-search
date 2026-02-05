from PIL import Image


class EmbeddingService:
    """CLIP 모델 기반 임베딩 서비스. M2~M3에서 구현 예정."""

    async def embed_image(self, image: Image.Image) -> list[float]:
        """이미지를 CLIP 임베딩 벡터로 변환."""
        raise NotImplementedError("M3에서 구현 예정")

    async def embed_text(self, text: str) -> list[float]:
        """텍스트를 CLIP 임베딩 벡터로 변환."""
        raise NotImplementedError("M3에서 구현 예정")
