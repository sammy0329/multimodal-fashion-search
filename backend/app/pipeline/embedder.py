"""CLIP 배치 임베딩 모듈.

이미지를 CLIP ViT-B/32 모델로 임베딩하고 .npy 캐시를 지원한다.
"""

import logging
from pathlib import Path

import numpy as np
import torch
from PIL import Image

logger = logging.getLogger(__name__)


class CLIPEmbedder:
    """CLIP ViT-B/32 기반 이미지 임베딩 생성기.

    Args:
        device: torch 디바이스 ("cpu", "cuda", "mps")
        cache_dir: .npy 캐시 디렉토리 (None이면 캐시 비활성화)
    """

    def __init__(
        self,
        device: str | None = None,
        cache_dir: Path | None = None,
    ) -> None:
        import clip

        if device is None:
            if torch.cuda.is_available():
                device = "cuda"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                device = "mps"
            else:
                device = "cpu"

        self.device = device
        self.cache_dir = cache_dir
        if cache_dir:
            cache_dir.mkdir(parents=True, exist_ok=True)

        logger.info("CLIP 모델 로드 중 (디바이스: %s)...", device)
        self.model, self.preprocess = clip.load("ViT-B/32", device=device)
        self.model.eval()
        logger.info("CLIP 모델 로드 완료")

    def _cache_path(self, image_id: int) -> Path | None:
        """캐시 파일 경로를 반환한다."""
        if self.cache_dir is None:
            return None
        return self.cache_dir / f"{image_id}.npy"

    def _load_cache(self, image_id: int) -> np.ndarray | None:
        """캐시된 임베딩을 로드한다."""
        cache_path = self._cache_path(image_id)
        if cache_path and cache_path.exists():
            return np.load(cache_path)
        return None

    def _save_cache(self, image_id: int, embedding: np.ndarray) -> None:
        """임베딩을 캐시에 저장한다."""
        cache_path = self._cache_path(image_id)
        if cache_path:
            np.save(cache_path, embedding)

    def embed_image(self, image_path: Path) -> np.ndarray:
        """단일 이미지를 임베딩한다.

        Args:
            image_path: 이미지 파일 경로

        Returns:
            512차원 정규화된 임베딩 (numpy array)
        """
        image = Image.open(image_path).convert("RGB")
        image_input = self.preprocess(image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            features = self.model.encode_image(image_input)
            features = features / features.norm(dim=-1, keepdim=True)

        return features.cpu().numpy().flatten()

    def embed_batch(
        self,
        items: list[tuple[int, Path]],
        batch_size: int = 32,
    ) -> dict[int, np.ndarray]:
        """이미지 배치를 임베딩한다. 캐시된 결과가 있으면 재사용한다.

        Args:
            items: (image_id, image_path) 튜플 리스트
            batch_size: 배치 크기

        Returns:
            {image_id: 512차원 임베딩} 딕셔너리
        """
        results: dict[int, np.ndarray] = {}
        to_process: list[tuple[int, Path]] = []

        for image_id, image_path in items:
            cached = self._load_cache(image_id)
            if cached is not None:
                results[image_id] = cached
            else:
                to_process.append((image_id, image_path))

        if to_process:
            logger.info(
                "임베딩 생성: %d개 (캐시 히트: %d개)",
                len(to_process),
                len(results),
            )

        for i in range(0, len(to_process), batch_size):
            batch = to_process[i : i + batch_size]
            images = []
            valid_items: list[tuple[int, Path]] = []

            for image_id, image_path in batch:
                try:
                    image = Image.open(image_path).convert("RGB")
                    images.append(self.preprocess(image))
                    valid_items.append((image_id, image_path))
                except Exception:
                    logger.warning("이미지 로드 실패: %s", image_path)

            if not images:
                continue

            image_input = torch.stack(images).to(self.device)

            with torch.no_grad():
                features = self.model.encode_image(image_input)
                features = features / features.norm(dim=-1, keepdim=True)

            embeddings = features.cpu().numpy()

            for idx, (image_id, _) in enumerate(valid_items):
                embedding = embeddings[idx]
                results[image_id] = embedding
                self._save_cache(image_id, embedding)

            if (i + batch_size) % (batch_size * 10) == 0:
                logger.info(
                    "진행: %d/%d", min(i + batch_size, len(to_process)), len(to_process)
                )

        return results
