"""Supabase 데이터 로더 테스트.

실제 Supabase 연결 없이 mock으로 유닛 테스트한다.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.pipeline.schemas import ProductRecord

# 모듈을 먼저 import해야 patch가 올바르게 동작한다
import app.pipeline.loader_supabase as loader_module


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
        "image_url": "https://example.com/img.jpg",
    }
    defaults.update(kwargs)
    return ProductRecord(**defaults)


class TestSupabaseLoader:
    def _make_loader(self, mock_create: MagicMock) -> "loader_module.SupabaseLoader":
        """mock된 create_client로 SupabaseLoader를 생성한다."""
        mock_client = MagicMock()
        mock_create.return_value = mock_client
        mock_client.storage.get_bucket.return_value = MagicMock()
        with patch.object(loader_module, "create_client", mock_create):
            loader = loader_module.SupabaseLoader("http://test.supabase.co", "test-key")
        return loader

    def test_upsert_products_success(self) -> None:
        """upsert가 성공하면 적재 건수를 반환해야 한다."""
        mock_create = MagicMock()
        loader = self._make_loader(mock_create)

        mock_result = MagicMock()
        mock_result.data = [{"product_id": "kf_1002_dress"}]
        loader.client.table.return_value.upsert.return_value.execute.return_value = (
            mock_result
        )

        records = [_make_product()]
        count = loader.upsert_products(records)

        assert count == 1
        loader.client.table.assert_called_with("products")

    def test_upsert_products_batch(self) -> None:
        """여러 레코드를 배치로 upsert해야 한다."""
        mock_create = MagicMock()
        loader = self._make_loader(mock_create)

        mock_result = MagicMock()
        mock_result.data = [{}] * 2
        loader.client.table.return_value.upsert.return_value.execute.return_value = (
            mock_result
        )

        records = [_make_product(product_id=f"kf_{i}_top") for i in range(3)]
        count = loader.upsert_products(records, batch_size=2)

        # 2개 배치: [2건] + [1건]
        assert count >= 3

    def test_upsert_products_handles_error(self) -> None:
        """upsert 실패 시 에러를 로깅하고 0을 반환해야 한다."""
        mock_create = MagicMock()
        loader = self._make_loader(mock_create)

        loader.client.table.return_value.upsert.return_value.execute.side_effect = (
            Exception("DB error")
        )

        records = [_make_product()]
        count = loader.upsert_products(records)

        assert count == 0

    def test_upload_image(self, tmp_path: Path) -> None:
        """이미지 업로드가 공개 URL을 반환해야 한다."""
        mock_create = MagicMock()
        loader = self._make_loader(mock_create)

        loader.client.storage.from_.return_value.get_public_url.return_value = (
            "https://storage.supabase.co/product-images/retro/123.jpg"
        )

        img_path = tmp_path / "test.jpg"
        img_path.write_bytes(b"fake image data")

        url = loader.upload_image(img_path, "retro/123.jpg")
        assert "123.jpg" in url

    def test_product_record_to_dict(self) -> None:
        """to_supabase_dict()가 올바른 필드를 포함해야 한다."""
        product = _make_product()
        d = product.to_supabase_dict()

        assert d["product_id"] == "kf_1002_dress"
        assert d["name"] == "Romantic Pink Dress"
        assert d["price"] == 67_000
        assert d["is_soldout"] is False
        assert d["data_source"] == "k-fashion"
        assert isinstance(d["style_tags"], list)
