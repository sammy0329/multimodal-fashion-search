"""Supabase 데이터 로더.

ProductRecord를 Supabase PostgreSQL에 upsert하고,
이미지를 Supabase Storage에 업로드한다.
"""

import logging
from pathlib import Path

from supabase import create_client

from app.pipeline.schemas import ProductRecord

logger = logging.getLogger(__name__)


class SupabaseLoader:
    """Supabase products 테이블 적재 및 이미지 업로드.

    Args:
        supabase_url: Supabase 프로젝트 URL
        supabase_key: Supabase service_role 키
        storage_bucket: Storage 버킷 이름
    """

    def __init__(
        self,
        supabase_url: str,
        supabase_key: str,
        storage_bucket: str = "product-images",
    ) -> None:
        self.client = create_client(supabase_url, supabase_key)
        self.storage_bucket = storage_bucket
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        """Storage 버킷이 없으면 생성한다."""
        try:
            self.client.storage.get_bucket(self.storage_bucket)
        except Exception:
            try:
                self.client.storage.create_bucket(
                    self.storage_bucket,
                    options={"public": True},
                )
                logger.info("Storage 버킷 생성: %s", self.storage_bucket)
            except Exception as e:
                logger.warning("버킷 생성 실패 (이미 존재할 수 있음): %s", e)

    def upload_image(self, image_path: Path, storage_path: str) -> str:
        """이미지를 Supabase Storage에 업로드하고 공개 URL을 반환한다.

        Args:
            image_path: 로컬 이미지 파일 경로
            storage_path: Storage 내 파일 경로 (예: "retro/1029079.jpg")

        Returns:
            공개 접근 가능한 이미지 URL
        """
        with open(image_path, "rb") as f:
            image_bytes = f.read()

        content_type = "image/jpeg"
        if image_path.suffix.lower() == ".png":
            content_type = "image/png"

        try:
            self.client.storage.from_(self.storage_bucket).upload(
                storage_path,
                image_bytes,
                file_options={"content-type": content_type, "upsert": "true"},
            )
        except Exception as e:
            logger.warning("이미지 업로드 실패 (%s): %s", storage_path, e)

        public_url = self.client.storage.from_(
            self.storage_bucket
        ).get_public_url(storage_path)

        return public_url

    def upsert_products(
        self,
        records: list[ProductRecord],
        batch_size: int = 100,
    ) -> int:
        """ProductRecord 리스트를 products 테이블에 upsert한다.

        Args:
            records: 적재할 ProductRecord 리스트
            batch_size: 배치 크기

        Returns:
            적재 성공 건수
        """
        total_upserted = 0

        for i in range(0, len(records), batch_size):
            batch = records[i : i + batch_size]
            rows = [r.to_supabase_dict() for r in batch]

            try:
                result = (
                    self.client.table("products")
                    .upsert(rows, on_conflict="product_id")
                    .execute()
                )
                total_upserted += len(result.data)
            except Exception as e:
                logger.error("Supabase upsert 실패 (배치 %d): %s", i // batch_size, e)

        logger.info("Supabase 적재 완료: %d/%d건", total_upserted, len(records))
        return total_upserted
