"""EmbeddingService 유닛 테스트.

CLIP 모델을 mock하여 임베딩 로직만 검증한다.
torch가 설치되지 않은 환경에서는 combine_embeddings 테스트만 실행한다.
"""

import sys
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from PIL import Image

from app.services.embedding import EMBEDDING_DIM, EmbeddingService

torch = pytest.importorskip("torch", reason="torch 미설치 - CLIP 테스트 건너뜀")


def _make_fake_features(dim: int = EMBEDDING_DIM) -> "torch.Tensor":
    """정규화된 가짜 feature 텐서를 생성한다."""
    values = np.random.randn(1, dim).astype(np.float32)
    norm = np.linalg.norm(values, axis=-1, keepdims=True)
    values = values / norm
    return torch.tensor(values)


def _build_embedding_service() -> EmbeddingService:
    """Mock CLIP으로 EmbeddingService를 생성한다."""
    mock_clip = MagicMock()
    mock_model = MagicMock()
    mock_model.eval.return_value = mock_model
    mock_preprocess = MagicMock()
    mock_clip.load.return_value = (mock_model, mock_preprocess)

    with patch.dict(sys.modules, {"clip": mock_clip}):
        service = EmbeddingService(device="cpu")

    service._clip = mock_clip
    return service


@pytest.fixture
def embedding_service():
    return _build_embedding_service()


class TestEmbedImageSync:
    def test_returns_list_of_correct_dimension(self, embedding_service):
        fake_features = _make_fake_features()
        embedding_service.model.encode_image.return_value = fake_features

        mock_tensor = MagicMock()
        mock_tensor.unsqueeze.return_value = mock_tensor
        mock_tensor.to.return_value = mock_tensor
        embedding_service.preprocess.return_value = mock_tensor

        image = Image.new("RGB", (224, 224))
        result = embedding_service._embed_image_sync(image)

        assert isinstance(result, list)
        assert len(result) == EMBEDDING_DIM

    def test_embedding_is_normalized(self, embedding_service):
        fake_features = _make_fake_features()
        embedding_service.model.encode_image.return_value = fake_features

        mock_tensor = MagicMock()
        mock_tensor.unsqueeze.return_value = mock_tensor
        mock_tensor.to.return_value = mock_tensor
        embedding_service.preprocess.return_value = mock_tensor

        image = Image.new("RGB", (224, 224))
        result = embedding_service._embed_image_sync(image)

        norm = np.linalg.norm(result)
        assert abs(norm - 1.0) < 1e-5


class TestEmbedTextSync:
    def test_returns_list_of_correct_dimension(self, embedding_service):
        fake_features = _make_fake_features()
        embedding_service.model.encode_text.return_value = fake_features

        mock_tokens = MagicMock()
        mock_tokens.to.return_value = mock_tokens
        embedding_service._clip.tokenize.return_value = mock_tokens

        result = embedding_service._embed_text_sync("오버핏 셔츠")

        assert isinstance(result, list)
        assert len(result) == EMBEDDING_DIM

    def test_embedding_is_normalized(self, embedding_service):
        fake_features = _make_fake_features()
        embedding_service.model.encode_text.return_value = fake_features

        mock_tokens = MagicMock()
        mock_tokens.to.return_value = mock_tokens
        embedding_service._clip.tokenize.return_value = mock_tokens

        result = embedding_service._embed_text_sync("레트로 드레스")

        norm = np.linalg.norm(result)
        assert abs(norm - 1.0) < 1e-5


class TestEmbedAsync:
    async def test_embed_image_async(self, embedding_service):
        fake_features = _make_fake_features()
        embedding_service.model.encode_image.return_value = fake_features

        mock_tensor = MagicMock()
        mock_tensor.unsqueeze.return_value = mock_tensor
        mock_tensor.to.return_value = mock_tensor
        embedding_service.preprocess.return_value = mock_tensor

        image = Image.new("RGB", (224, 224))
        result = await embedding_service.embed_image(image)

        assert isinstance(result, list)
        assert len(result) == EMBEDDING_DIM

    async def test_embed_text_async(self, embedding_service):
        fake_features = _make_fake_features()
        embedding_service.model.encode_text.return_value = fake_features

        mock_tokens = MagicMock()
        mock_tokens.to.return_value = mock_tokens
        embedding_service._clip.tokenize.return_value = mock_tokens

        result = await embedding_service.embed_text("캐주얼 셔츠")

        assert isinstance(result, list)
        assert len(result) == EMBEDDING_DIM


class TestCombineEmbeddings:
    def test_returns_correct_dimension(self):
        img_emb = np.random.randn(EMBEDDING_DIM).tolist()
        txt_emb = np.random.randn(EMBEDDING_DIM).tolist()

        result = EmbeddingService.combine_embeddings(img_emb, txt_emb)

        assert len(result) == EMBEDDING_DIM

    def test_result_is_normalized(self):
        img_emb = np.random.randn(EMBEDDING_DIM).tolist()
        txt_emb = np.random.randn(EMBEDDING_DIM).tolist()

        result = EmbeddingService.combine_embeddings(img_emb, txt_emb)

        norm = np.linalg.norm(result)
        assert abs(norm - 1.0) < 1e-5

    def test_image_weight_dominates(self):
        img_emb = [1.0] + [0.0] * (EMBEDDING_DIM - 1)
        txt_emb = [0.0] + [1.0] + [0.0] * (EMBEDDING_DIM - 2)

        result = EmbeddingService.combine_embeddings(
            img_emb, txt_emb, image_weight=0.9, text_weight=0.1
        )

        assert result[0] > result[1]

    def test_zero_vectors(self):
        zero = [0.0] * EMBEDDING_DIM
        result = EmbeddingService.combine_embeddings(zero, zero)
        assert all(v == 0.0 for v in result)

    def test_custom_weights(self):
        img_emb = [1.0] + [0.0] * (EMBEDDING_DIM - 1)
        txt_emb = [0.0] + [1.0] + [0.0] * (EMBEDDING_DIM - 2)

        result = EmbeddingService.combine_embeddings(
            img_emb, txt_emb, image_weight=0.5, text_weight=0.5
        )

        assert abs(result[0] - result[1]) < 1e-5
