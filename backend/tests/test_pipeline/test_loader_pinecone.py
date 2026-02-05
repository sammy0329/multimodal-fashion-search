"""Pinecone 데이터 로더 테스트.

실제 Pinecone 연결 없이 mock으로 유닛 테스트한다.
"""

from unittest.mock import MagicMock, patch

import numpy as np

from app.pipeline.schemas import PineconeRecord, ProductRecord

import app.pipeline.loader_pinecone as loader_module


def _make_product(**kwargs) -> ProductRecord:
    """테스트용 ProductRecord를 생성한다."""
    defaults = {
        "product_id": "kf_1002_dress",
        "name": "Romantic Pink Dress",
        "name_ko": "로맨틱 핑크 드레스",
        "price": 67_000,
        "brand": "BLOOM ATELIER",
        "category": "원피스",
        "sub_category": "드레스",
        "style_tags": ["로맨틱"],
        "color": "핑크",
    }
    defaults.update(kwargs)
    return ProductRecord(**defaults)


class TestPineconeLoader:
    def _make_loader(self) -> "loader_module.PineconeLoader":
        """mock된 Pinecone 클라이언트로 PineconeLoader를 생성한다."""
        mock_pc = MagicMock()
        mock_index = MagicMock()
        mock_pc.return_value.Index.return_value = mock_index
        with patch.object(loader_module, "Pinecone", mock_pc):
            loader = loader_module.PineconeLoader(api_key="test-key")
        return loader

    def test_build_pinecone_record(self) -> None:
        """ProductRecord와 임베딩으로 PineconeRecord를 올바르게 생성해야 한다."""
        loader = self._make_loader()
        product = _make_product()
        embedding = np.random.rand(512).astype(np.float32)

        record = loader.build_pinecone_record(product, embedding)

        assert record.id == "product_kf_1002_dress"
        assert len(record.values) == 512
        assert record.metadata["category"] == "원피스"
        assert record.metadata["price"] == 67_000
        assert record.metadata["brand"] == "BLOOM ATELIER"

    def test_upsert_vectors_success(self) -> None:
        """upsert가 성공하면 적재 건수를 반환해야 한다."""
        loader = self._make_loader()

        records = [
            PineconeRecord(
                id=f"product_kf_{i}_top",
                values=[0.1] * 512,
                metadata={"category": "상의"},
            )
            for i in range(3)
        ]

        count = loader.upsert_vectors(records)
        assert count == 3
        loader.index.upsert.assert_called_once()

    def test_upsert_vectors_batch(self) -> None:
        """여러 배치로 나누어 upsert해야 한다."""
        loader = self._make_loader()

        records = [
            PineconeRecord(
                id=f"product_kf_{i}_top",
                values=[0.1] * 512,
                metadata={"category": "상의"},
            )
            for i in range(5)
        ]

        count = loader.upsert_vectors(records, batch_size=2)
        assert count == 5
        assert loader.index.upsert.call_count == 3  # 2 + 2 + 1

    def test_upsert_vectors_handles_error(self) -> None:
        """upsert 실패 시 에러를 로깅하고 0을 반환해야 한다."""
        loader = self._make_loader()
        loader.index.upsert.side_effect = Exception("Pinecone error")

        records = [
            PineconeRecord(
                id="product_kf_1_top",
                values=[0.1] * 512,
                metadata={"category": "상의"},
            )
        ]

        count = loader.upsert_vectors(records)
        assert count == 0

    def test_pinecone_record_to_dict(self) -> None:
        """to_pinecone_dict()가 올바른 구조를 반환해야 한다."""
        record = PineconeRecord(
            id="product_kf_1002_dress",
            values=[0.5] * 512,
            metadata={"category": "원피스", "price": 67_000},
        )
        d = record.to_pinecone_dict()

        assert d["id"] == "product_kf_1002_dress"
        assert len(d["values"]) == 512
        assert d["metadata"]["category"] == "원피스"

    def test_build_record_metadata_completeness(self) -> None:
        """메타데이터에 필수 필드가 모두 포함되어야 한다."""
        loader = self._make_loader()
        product = _make_product(season="여름")
        embedding = np.random.rand(512).astype(np.float32)

        record = loader.build_pinecone_record(product, embedding)

        required_fields = [
            "category", "sub_category", "style_tags", "color",
            "season", "price", "brand", "data_source", "is_soldout",
        ]
        for field in required_fields:
            assert field in record.metadata, f"메타데이터에 {field}가 없음"
