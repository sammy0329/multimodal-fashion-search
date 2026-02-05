"""Pinecone 'style-matcher' 인덱스 생성 스크립트.

사용법:
    python scripts/init_pinecone.py

환경변수:
    PINECONE_API_KEY: Pinecone API 키
    PINECONE_INDEX: 인덱스 이름 (기본값: style-matcher)
"""

import os
import sys

from pinecone import Pinecone, ServerlessSpec

DIMENSION = 512  # CLIP ViT-B/32 임베딩 차원
METRIC = "cosine"
CLOUD = "aws"
REGION = "us-east-1"


def main() -> None:
    api_key = os.environ.get("PINECONE_API_KEY")
    if not api_key:
        print("PINECONE_API_KEY 환경변수가 설정되지 않았습니다.")
        sys.exit(1)

    index_name = os.environ.get("PINECONE_INDEX", "style-matcher")

    pc = Pinecone(api_key=api_key)

    existing_indexes = [idx.name for idx in pc.list_indexes()]
    if index_name in existing_indexes:
        print(f"인덱스 '{index_name}'이(가) 이미 존재합니다. 건너뜁니다.")
        return

    print(f"인덱스 '{index_name}' 생성 중... (dimension={DIMENSION}, metric={METRIC})")
    pc.create_index(
        name=index_name,
        dimension=DIMENSION,
        metric=METRIC,
        spec=ServerlessSpec(cloud=CLOUD, region=REGION),
    )
    print(f"인덱스 '{index_name}' 생성 완료.")


if __name__ == "__main__":
    main()
