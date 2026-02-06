"""CLIP 모델 기반 임베딩 서비스.

이미지와 텍스트를 동일한 512차원 벡터 공간에 매핑한다.
"""

from __future__ import annotations

import asyncio
import logging
import os
from functools import partial
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from PIL import Image

logger = logging.getLogger(__name__)

EMBEDDING_DIM = 512
IMAGE_WEIGHT = 0.6
TEXT_WEIGHT = 0.4


class EmbeddingService:
    """CLIP ViT-B/32 기반 임베딩 서비스.

    Args:
        device: torch 디바이스 ("cpu", "cuda", "mps").
            None이면 자동 감지.
    """

    def __init__(self, device: str | None = None) -> None:
        self._mock_mode = os.getenv("EMBEDDING_MOCK", "").lower() in ("1", "true")

        if self._mock_mode:
            logger.warning("임베딩 서비스 MOCK 모드 - 랜덤 벡터 반환")
            self.device = "cpu"
            self._clip = None
            self._torch = None
            self.model = None
            self.preprocess = None
            return

        import clip
        import torch

        if device is None:
            if torch.cuda.is_available():
                device = "cuda"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                device = "mps"
            else:
                device = "cpu"

        self.device = device
        self._clip = clip
        self._torch = torch

        logger.info("CLIP 모델 로드 중 (디바이스: %s)...", device)
        self.model, self.preprocess = clip.load("ViT-B/32", device=device)
        self.model.eval()
        logger.info("CLIP 모델 로드 완료")

    def _generate_mock_embedding(self, seed: int = 0) -> list[float]:
        """Mock 모드용 랜덤 임베딩 생성."""
        rng = np.random.default_rng(seed)
        vec = rng.random(EMBEDDING_DIM).astype(np.float32)
        vec = vec / np.linalg.norm(vec)
        return vec.tolist()

    def _embed_image_sync(self, image: Image.Image) -> list[float]:
        """이미지를 512차원 CLIP 임베딩으로 변환한다 (동기)."""
        if self._mock_mode:
            return self._generate_mock_embedding(hash(str(image.size)) % 10000)

        image_input = self.preprocess(image).unsqueeze(0).to(self.device)

        with self._torch.no_grad():
            features = self.model.encode_image(image_input)
            features = features / features.norm(dim=-1, keepdim=True)

        return features.cpu().numpy().flatten().tolist()

    def _embed_text_sync(self, text: str) -> list[float]:
        """텍스트를 512차원 CLIP 임베딩으로 변환한다 (동기)."""
        if self._mock_mode:
            return self._generate_mock_embedding(hash(text) % 10000)

        tokens = self._clip.tokenize([text], truncate=True).to(self.device)

        with self._torch.no_grad():
            features = self.model.encode_text(tokens)
            features = features / features.norm(dim=-1, keepdim=True)

        return features.cpu().numpy().flatten().tolist()

    async def embed_image(self, image: Image.Image) -> list[float]:
        """이미지를 CLIP 임베딩 벡터로 변환한다.

        Args:
            image: RGB PIL Image.

        Returns:
            512차원 정규화된 임베딩 벡터.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(self._embed_image_sync, image))

    async def embed_text(self, text: str) -> list[float]:
        """텍스트를 CLIP 임베딩 벡터로 변환한다.

        Args:
            text: 검색 쿼리 텍스트.

        Returns:
            512차원 정규화된 임베딩 벡터.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(self._embed_text_sync, text))

    @staticmethod
    def combine_embeddings(
        image_embedding: list[float],
        text_embedding: list[float],
        image_weight: float = IMAGE_WEIGHT,
        text_weight: float = TEXT_WEIGHT,
    ) -> list[float]:
        """이미지와 텍스트 임베딩을 가중 평균으로 결합한다.

        Args:
            image_embedding: 이미지 임베딩 벡터.
            text_embedding: 텍스트 임베딩 벡터.
            image_weight: 이미지 가중치 (기본 0.6).
            text_weight: 텍스트 가중치 (기본 0.4).

        Returns:
            결합 후 재정규화된 512차원 벡터.
        """
        img_vec = np.array(image_embedding)
        txt_vec = np.array(text_embedding)

        hybrid = image_weight * img_vec + text_weight * txt_vec
        norm = np.linalg.norm(hybrid)
        if norm > 0:
            hybrid = hybrid / norm

        return hybrid.tolist()
