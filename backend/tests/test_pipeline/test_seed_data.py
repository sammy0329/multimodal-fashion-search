"""데이터 파이프라인 오케스트레이터 테스트.

실제 외부 서비스 연결 없이 mock으로 유닛 테스트한다.
"""

import json
from argparse import Namespace
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from app.core.config import Settings

import scripts.seed_data as seed_module


# -- 테스트용 샘플 데이터 생성 헬퍼 --

SAMPLE_LABEL = {
    "이미지 정보": {"이미지 식별자": 100, "이미지 파일명": "100.jpg"},
    "데이터셋 정보": {
        "데이터셋 상세설명": {
            "라벨링": {
                "스타일": [{"스타일": "레트로", "서브스타일": "페미닌"}],
                "상의": [{"카테고리": "티셔츠", "색상": "블랙"}],
                "하의": [{}],
                "아우터": [{}],
                "원피스": [{}],
            }
        }
    },
}


def _create_sample_data(tmp_path: Path) -> Path:
    """테스트용 샘플 데이터 디렉토리를 생성한다."""
    data_dir = tmp_path / "sample-data"

    label_dir = data_dir / "라벨링데이터" / "레트로"
    label_dir.mkdir(parents=True)

    image_dir = data_dir / "원천데이터" / "레트로"
    image_dir.mkdir(parents=True)

    (label_dir / "100.json").write_text(
        json.dumps(SAMPLE_LABEL, ensure_ascii=False), encoding="utf-8"
    )
    (image_dir / "100.jpg").write_bytes(b"fake image")

    return data_dir


# -- CLI 인자 파싱 테스트 --


class TestParseArgs:
    def test_required_data_dir(self) -> None:
        """--data-dir 없이 실행하면 SystemExit이 발생해야 한다."""
        with pytest.raises(SystemExit):
            seed_module.parse_args([])

    def test_default_values(self) -> None:
        """기본값이 올바르게 설정되어야 한다."""
        args = seed_module.parse_args(["--data-dir", "/tmp/data"])

        assert args.data_dir == Path("/tmp/data")
        assert args.dry_run is False
        assert args.skip_embedding is False
        assert args.skip_upload is False
        assert args.batch_size is None
        assert args.cache_dir is None
        assert args.device is None
        assert args.log_level == "INFO"

    def test_all_flags(self) -> None:
        """모든 플래그가 올바르게 파싱되어야 한다."""
        args = seed_module.parse_args([
            "--data-dir", "/tmp/data",
            "--dry-run",
            "--skip-embedding",
            "--skip-upload",
            "--batch-size", "64",
            "--cache-dir", "/tmp/cache",
            "--device", "cpu",
            "--log-level", "DEBUG",
        ])

        assert args.dry_run is True
        assert args.skip_embedding is True
        assert args.skip_upload is True
        assert args.batch_size == 64
        assert args.cache_dir == Path("/tmp/cache")
        assert args.device == "cpu"
        assert args.log_level == "DEBUG"


# -- dry-run 테스트 --


class TestDryRun:
    def test_dry_run_parses_without_db(self, tmp_path: Path) -> None:
        """dry-run은 DB 연결 없이 파싱 결과만 반환해야 한다."""
        data_dir = _create_sample_data(tmp_path)

        args = Namespace(
            data_dir=data_dir,
            dry_run=True,
            skip_embedding=True,
            skip_upload=True,
            batch_size=None,
            cache_dir=None,
            device=None,
        )

        result = seed_module.run_pipeline(args, settings=Settings())

        assert result["products_parsed"] == 1
        assert result["unique_images"] == 1
        assert result["supabase_upserted"] == 0
        assert result["pinecone_upserted"] == 0


# -- 파이프라인 통합 테스트 (모든 외부 의존성 mock) --


class TestRunPipeline:
    def _make_settings(self) -> Settings:
        """테스트용 Settings를 생성한다."""
        return Settings(
            supabase_url="http://test.supabase.co",
            supabase_service_key="test-key",
            pinecone_api_key="test-pinecone-key",
            pinecone_index="test-index",
            clip_batch_size=16,
        )

    def test_skip_embedding_and_upload(self, tmp_path: Path) -> None:
        """임베딩/업로드 스킵 시 Supabase만 적재해야 한다."""
        data_dir = _create_sample_data(tmp_path)

        args = Namespace(
            data_dir=data_dir,
            dry_run=False,
            skip_embedding=True,
            skip_upload=True,
            batch_size=None,
            cache_dir=None,
            device=None,
        )

        mock_sb_class = MagicMock()
        mock_sb_instance = MagicMock()
        mock_sb_class.return_value = mock_sb_instance
        mock_sb_instance.upsert_products.return_value = 1

        with patch.object(seed_module, "SupabaseLoader", mock_sb_class, create=True):
            # SupabaseLoader is lazily imported, so patch at the import target
            with patch(
                "app.pipeline.loader_supabase.create_client", MagicMock()
            ):
                import app.pipeline.loader_supabase as sb_mod

                with patch.object(sb_mod, "SupabaseLoader", mock_sb_class):
                    # Patch the lazy import in seed_data
                    with patch.dict(
                        "sys.modules",
                        {"app.pipeline.loader_supabase": MagicMock(SupabaseLoader=mock_sb_class)},
                    ):
                        result = seed_module.run_pipeline(args, settings=self._make_settings())

        assert result["products_parsed"] == 1
        assert result["images_embedded"] == 0
        assert result["images_uploaded"] == 0

    def test_full_pipeline_with_mocks(self, tmp_path: Path) -> None:
        """전체 파이프라인이 mock으로 정상 동작해야 한다."""
        data_dir = _create_sample_data(tmp_path)

        args = Namespace(
            data_dir=data_dir,
            dry_run=False,
            skip_embedding=False,
            skip_upload=False,
            batch_size=16,
            cache_dir=None,
            device="cpu",
        )

        # Mock CLIPEmbedder
        mock_embedder_class = MagicMock()
        mock_embedder = MagicMock()
        mock_embedder_class.return_value = mock_embedder
        mock_embedder.embed_batch.return_value = {
            100: np.random.rand(512).astype(np.float32),
        }

        # Mock SupabaseLoader
        mock_sb_class = MagicMock()
        mock_sb_instance = MagicMock()
        mock_sb_class.return_value = mock_sb_instance
        mock_sb_instance.upload_image.return_value = "https://storage.test/img.jpg"
        mock_sb_instance.upsert_products.return_value = 1

        # Mock PineconeLoader
        mock_pc_class = MagicMock()
        mock_pc_instance = MagicMock()
        mock_pc_class.return_value = mock_pc_instance
        mock_pc_instance.build_pinecone_record.return_value = MagicMock()
        mock_pc_instance.upsert_vectors.return_value = 1

        with (
            patch.dict(
                "sys.modules",
                {
                    "app.pipeline.embedder": MagicMock(CLIPEmbedder=mock_embedder_class),
                    "app.pipeline.loader_supabase": MagicMock(
                        SupabaseLoader=mock_sb_class
                    ),
                    "app.pipeline.loader_pinecone": MagicMock(
                        PineconeLoader=mock_pc_class
                    ),
                },
            ),
        ):
            result = seed_module.run_pipeline(args, settings=self._make_settings())

        assert result["products_parsed"] == 1
        assert result["unique_images"] == 1
        assert result["images_embedded"] == 1
        assert result["images_uploaded"] == 1
        assert result["supabase_upserted"] == 1
        assert result["pinecone_upserted"] == 1


class TestParseAllProducts:
    def test_extracts_products_from_sample(self, tmp_path: Path) -> None:
        """샘플 데이터에서 상품 레코드를 올바르게 추출해야 한다."""
        data_dir = _create_sample_data(tmp_path)

        product_items, unique_images = seed_module._parse_all_products(data_dir)

        assert len(product_items) == 1
        product, image_path, image_id = product_items[0]

        assert product.product_id == "kf_100_top"
        assert product.category == "상의"
        assert product.sub_category == "티셔츠"
        assert image_id == 100
        assert 100 in unique_images

    def test_multiple_garments(self, tmp_path: Path) -> None:
        """이미지 하나에 여러 의류가 있으면 모두 추출해야 한다."""
        data_dir = tmp_path / "multi"
        label_dir = data_dir / "라벨링데이터" / "레트로"
        label_dir.mkdir(parents=True)
        image_dir = data_dir / "원천데이터" / "레트로"
        image_dir.mkdir(parents=True)

        multi_label = {
            "이미지 정보": {"이미지 식별자": 200, "이미지 파일명": "200.jpg"},
            "데이터셋 정보": {
                "데이터셋 상세설명": {
                    "라벨링": {
                        "스타일": [{"스타일": "레트로", "서브스타일": "페미닌"}],
                        "상의": [{"카테고리": "셔츠", "색상": "화이트"}],
                        "하의": [{"카테고리": "팬츠", "색상": "블랙"}],
                        "아우터": [{"카테고리": "재킷", "색상": "그레이"}],
                        "원피스": [{}],
                    }
                }
            },
        }

        (label_dir / "200.json").write_text(
            json.dumps(multi_label, ensure_ascii=False), encoding="utf-8"
        )
        (image_dir / "200.jpg").write_bytes(b"fake image")

        product_items, unique_images = seed_module._parse_all_products(data_dir)

        assert len(product_items) == 3
        assert len(unique_images) == 1

        product_ids = {p.product_id for p, _, _ in product_items}
        assert "kf_200_top" in product_ids
        assert "kf_200_bottom" in product_ids
        assert "kf_200_outer" in product_ids
