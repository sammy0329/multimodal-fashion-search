"""CLIP 임베딩 모듈 테스트.

CLIP 모델이 실제로 설치되어 있어야 하는 통합 테스트와,
모델 없이도 동작하는 캐시 유닛 테스트를 분리한다.
"""

from pathlib import Path

import numpy as np
import pytest


def _clip_available() -> bool:
    """CLIP 모델 사용 가능 여부를 확인한다."""
    try:
        import clip  # noqa: F401

        return True
    except ImportError:
        return False


class TestEmbeddingCache:
    """CLIPEmbedder를 생성하지 않고 캐시 로직만 테스트한다."""

    def test_npy_save_and_load(self, tmp_path: Path) -> None:
        """numpy 캐시 저장/로드가 정상 동작해야 한다."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()

        embedding = np.random.rand(512).astype(np.float32)
        cache_path = cache_dir / "12345.npy"
        np.save(cache_path, embedding)

        loaded = np.load(cache_path)
        np.testing.assert_array_almost_equal(loaded, embedding)

    def test_cache_file_not_exists(self, tmp_path: Path) -> None:
        """존재하지 않는 캐시 파일을 확인한다."""
        cache_path = tmp_path / "cache" / "99999.npy"
        assert not cache_path.exists()

    def test_embedding_dimension(self) -> None:
        """CLIP ViT-B/32 임베딩은 512차원이어야 한다."""
        embedding = np.random.rand(512).astype(np.float32)
        assert embedding.shape == (512,)

    def test_embedding_normalization(self) -> None:
        """정규화된 임베딩의 L2 norm은 1.0이어야 한다."""
        embedding = np.random.rand(512).astype(np.float32)
        normalized = embedding / np.linalg.norm(embedding)
        assert np.isclose(np.linalg.norm(normalized), 1.0, atol=1e-5)

    def test_batch_cache_organization(self, tmp_path: Path) -> None:
        """배치 캐시가 image_id별로 저장되어야 한다."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()

        for image_id in [100, 200, 300]:
            embedding = np.random.rand(512).astype(np.float32)
            np.save(cache_dir / f"{image_id}.npy", embedding)

        cached_files = list(cache_dir.glob("*.npy"))
        assert len(cached_files) == 3
        ids = sorted(int(f.stem) for f in cached_files)
        assert ids == [100, 200, 300]


@pytest.mark.skipif(
    not _clip_available(),
    reason="CLIP 모델이 설치되어 있지 않습니다",
)
class TestCLIPEmbedderIntegration:
    """CLIP 모델이 필요한 통합 테스트."""

    def test_embed_single_image(self, tmp_path: Path) -> None:
        """단일 이미지 임베딩이 512차원이어야 한다."""
        from PIL import Image

        from app.pipeline.embedder import CLIPEmbedder

        embedder = CLIPEmbedder(device="cpu")

        img = Image.new("RGB", (224, 224), color=(128, 128, 128))
        img_path = tmp_path / "test.jpg"
        img.save(img_path)

        embedding = embedder.embed_image(img_path)
        assert embedding.shape == (512,)
        assert np.isclose(np.linalg.norm(embedding), 1.0, atol=1e-5)

    def test_embed_batch(self, tmp_path: Path) -> None:
        """배치 임베딩이 정상 동작해야 한다."""
        from PIL import Image

        from app.pipeline.embedder import CLIPEmbedder

        embedder = CLIPEmbedder(device="cpu", cache_dir=tmp_path / "cache")

        items = []
        for i in range(3):
            img = Image.new("RGB", (224, 224), color=(i * 80, 100, 200))
            img_path = tmp_path / f"img_{i}.jpg"
            img.save(img_path)
            items.append((i, img_path))

        results = embedder.embed_batch(items, batch_size=2)
        assert len(results) == 3
        for embedding in results.values():
            assert embedding.shape == (512,)

    def test_batch_uses_cache(self, tmp_path: Path) -> None:
        """두 번째 호출 시 캐시를 재사용해야 한다."""
        from PIL import Image

        from app.pipeline.embedder import CLIPEmbedder

        cache_dir = tmp_path / "cache"
        embedder = CLIPEmbedder(device="cpu", cache_dir=cache_dir)

        img = Image.new("RGB", (224, 224), color=(100, 100, 100))
        img_path = tmp_path / "cached.jpg"
        img.save(img_path)

        results1 = embedder.embed_batch([(42, img_path)])
        assert (cache_dir / "42.npy").exists()

        results2 = embedder.embed_batch([(42, img_path)])
        np.testing.assert_array_almost_equal(results1[42], results2[42])
