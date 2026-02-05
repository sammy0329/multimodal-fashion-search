"""Pinecone 벡터 데이터 로더.

ProductRecord와 CLIP 임베딩을 Pinecone에 upsert한다.
"""

import logging

import numpy as np
from pinecone import Pinecone

from app.pipeline.schemas import PineconeRecord, ProductRecord

logger = logging.getLogger(__name__)


class PineconeLoader:
    """Pinecone 벡터 적재기.

    Args:
        api_key: Pinecone API 키
        index_name: 인덱스 이름
    """

    def __init__(self, api_key: str, index_name: str = "style-matcher") -> None:
        self.pc = Pinecone(api_key=api_key)
        self.index = self.pc.Index(index_name)
        logger.info("Pinecone 인덱스 연결: %s", index_name)

    def build_pinecone_record(
        self,
        product: ProductRecord,
        embedding: np.ndarray,
    ) -> PineconeRecord:
        """ProductRecord와 임베딩으로 PineconeRecord를 생성한다.

        Args:
            product: 상품 레코드
            embedding: 512차원 CLIP 임베딩

        Returns:
            PineconeRecord
        """
        metadata = {
            "category": product.category,
            "sub_category": product.sub_category,
            "style_tags": product.style_tags,
            "color": product.color or "",
            "season": product.season or "",
            "price": product.price,
            "brand": product.brand,
            "data_source": product.data_source,
            "is_soldout": product.is_soldout,
        }

        return PineconeRecord(
            id=f"product_{product.product_id}",
            values=embedding.tolist(),
            metadata=metadata,
        )

    def upsert_vectors(
        self,
        records: list[PineconeRecord],
        batch_size: int = 100,
    ) -> int:
        """PineconeRecord 리스트를 인덱스에 upsert한다.

        Args:
            records: 적재할 PineconeRecord 리스트
            batch_size: 배치 크기

        Returns:
            적재 성공 건수
        """
        total_upserted = 0

        for i in range(0, len(records), batch_size):
            batch = records[i : i + batch_size]
            vectors = [r.to_pinecone_dict() for r in batch]

            try:
                self.index.upsert(vectors=vectors)
                total_upserted += len(batch)
            except Exception as e:
                logger.error("Pinecone upsert 실패 (배치 %d): %s", i // batch_size, e)

        logger.info("Pinecone 적재 완료: %d/%d건", total_upserted, len(records))
        return total_upserted
