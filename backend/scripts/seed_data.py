"""AI Hub K-Fashion 데이터 파이프라인 오케스트레이터.

데이터를 파싱 → CLIP 임베딩 → Supabase/Pinecone 적재한다.

Usage:
    # dry-run (파싱 결과만 확인)
    python -m scripts.seed_data --data-dir /path/to/data --dry-run

    # 스타일당 100개로 샘플링 (무료 티어 최적화)
    python -m scripts.seed_data --data-dir /path/to/data --limit-per-style 100 --dry-run

    # 전체 파이프라인 실행
    python -m scripts.seed_data --data-dir /path/to/data

    # 임베딩 스킵 (메타데이터만 적재)
    python -m scripts.seed_data --data-dir /path/to/data --skip-embedding

    # 이미지 업로드 스킵
    python -m scripts.seed_data --data-dir /path/to/data --skip-upload
"""

import argparse
import logging
import sys
from pathlib import Path

from app.core.config import Settings
from app.pipeline.name_generator import build_product_record
from app.pipeline.parser import extract_valid_garments, parse_label_file, scan_data_directory
from app.pipeline.schemas import ProductRecord

logger = logging.getLogger(__name__)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """CLI 인자를 파싱한다."""
    parser = argparse.ArgumentParser(
        description="AI Hub K-Fashion 데이터 파이프라인",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        required=True,
        help="샘플 데이터 루트 디렉토리",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="파싱만 수행하고 DB 적재를 스킵한다",
    )
    parser.add_argument(
        "--skip-embedding",
        action="store_true",
        help="CLIP 임베딩을 스킵한다 (메타데이터만 적재)",
    )
    parser.add_argument(
        "--skip-upload",
        action="store_true",
        help="Supabase Storage 이미지 업로드를 스킵한다",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
        help="CLIP 임베딩 배치 크기 (기본: 설정 파일 값)",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=None,
        help="임베딩 .npy 캐시 디렉토리",
    )
    parser.add_argument(
        "--device",
        choices=["cpu", "cuda", "mps"],
        default=None,
        help="torch 디바이스 (기본: 자동 감지)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="로그 레벨",
    )
    parser.add_argument(
        "--limit-per-style",
        type=int,
        default=None,
        help="스타일당 최대 샘플 수 (무료 티어 제한 시 사용, 예: 100)",
    )
    return parser.parse_args(argv)


def _parse_all_products(
    data_dir: Path,
    limit_per_style: int | None = None,
) -> tuple[list[tuple[ProductRecord, Path, int]], dict[int, Path]]:
    """데이터 디렉토리를 스캔하여 상품 레코드와 이미지 매핑을 반환한다.

    Args:
        data_dir: 데이터 루트 디렉토리
        limit_per_style: 스타일당 최대 샘플 수 (None이면 제한 없음)

    Returns:
        (product_items, unique_images)
        - product_items: (ProductRecord, image_path, image_id) 리스트
        - unique_images: {image_id: image_path} 딕셔너리
    """
    pairs = scan_data_directory(data_dir, limit_per_style=limit_per_style)

    product_items: list[tuple[ProductRecord, Path, int]] = []
    unique_images: dict[int, Path] = {}

    for label_path, image_path, _style_name in pairs:
        label = parse_label_file(label_path)
        if label is None:
            continue

        for garment_type, garment in extract_valid_garments(label):
            product = build_product_record(label, garment_type, garment)
            product_items.append((product, image_path, label.image_id))

        if label.image_id not in unique_images:
            unique_images[label.image_id] = image_path

    return product_items, unique_images


def _print_dry_run_summary(
    product_items: list[tuple[ProductRecord, Path, int]],
    unique_images: dict[int, Path],
) -> None:
    """dry-run 결과를 출력한다."""
    print(f"\n{'='*60}")
    print(f"  파싱 결과 요약 (dry-run)")
    print(f"{'='*60}")
    print(f"  상품 레코드: {len(product_items)}개")
    print(f"  고유 이미지: {len(unique_images)}개")

    # 카테고리별 집계
    categories: dict[str, int] = {}
    brands: dict[str, int] = {}
    for product, _, _ in product_items:
        categories[product.category] = categories.get(product.category, 0) + 1
        brands[product.brand] = brands.get(product.brand, 0) + 1

    print(f"\n  카테고리별:")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"    {cat}: {count}개")

    print(f"\n  브랜드별:")
    for brand, count in sorted(brands.items(), key=lambda x: -x[1]):
        print(f"    {brand}: {count}개")

    print(f"\n  샘플 (상위 5개):")
    for product, _, _ in product_items[:5]:
        print(
            f"    {product.product_id}: {product.name_ko}"
            f" | {product.brand} | {product.price:,}원"
        )
    print(f"{'='*60}\n")


def run_pipeline(args: argparse.Namespace, settings: Settings | None = None) -> dict:
    """파이프라인을 실행한다.

    Args:
        args: CLI 인자
        settings: 설정 (None이면 환경변수에서 로드)

    Returns:
        실행 결과 요약 딕셔너리
    """
    if settings is None:
        settings = Settings()

    result = {
        "products_parsed": 0,
        "unique_images": 0,
        "images_uploaded": 0,
        "images_embedded": 0,
        "supabase_upserted": 0,
        "pinecone_upserted": 0,
    }

    # Step 1: 데이터 파싱
    limit = args.limit_per_style
    if limit:
        logger.info("Step 1: 데이터 파싱 시작 (스타일당 최대 %d개)...", limit)
    else:
        logger.info("Step 1: 데이터 파싱 시작...")
    product_items, unique_images = _parse_all_products(args.data_dir, limit_per_style=limit)
    result["products_parsed"] = len(product_items)
    result["unique_images"] = len(unique_images)

    logger.info(
        "파싱 완료: 상품 %d개, 고유 이미지 %d개",
        len(product_items),
        len(unique_images),
    )

    if args.dry_run:
        _print_dry_run_summary(product_items, unique_images)
        return result

    # Step 2: CLIP 임베딩
    embeddings: dict = {}
    if not args.skip_embedding:
        from app.pipeline.embedder import CLIPEmbedder

        device = args.device or settings.clip_device or None
        batch_size = args.batch_size or settings.clip_batch_size

        logger.info("Step 2: CLIP 임베딩 시작 (디바이스: %s)...", device or "auto")
        embedder = CLIPEmbedder(device=device, cache_dir=args.cache_dir)
        image_list = list(unique_images.items())
        embeddings = embedder.embed_batch(image_list, batch_size=batch_size)
        result["images_embedded"] = len(embeddings)
        logger.info("임베딩 완료: %d개", len(embeddings))
    else:
        logger.info("Step 2: CLIP 임베딩 스킵")

    # Step 3: Supabase Storage 이미지 업로드
    image_urls: dict[str, str] = {}
    sb_loader = None

    if not args.skip_upload:
        from app.pipeline.loader_supabase import SupabaseLoader

        logger.info("Step 3: 이미지 업로드 시작...")
        sb_loader = SupabaseLoader(
            settings.supabase_url,
            settings.supabase_service_key,
            settings.supabase_storage_bucket,
        )
        for product, image_path, _image_id in product_items:
            storage_path = f"{product.category}/{product.product_id}.jpg"
            url = sb_loader.upload_image(image_path, storage_path)
            image_urls[product.product_id] = url

        result["images_uploaded"] = len(image_urls)
        logger.info("이미지 업로드 완료: %d개", len(image_urls))
    else:
        logger.info("Step 3: 이미지 업로드 스킵")

    # Step 4: Supabase products 테이블 적재
    from app.pipeline.loader_supabase import SupabaseLoader

    if sb_loader is None:
        sb_loader = SupabaseLoader(
            settings.supabase_url,
            settings.supabase_service_key,
            settings.supabase_storage_bucket,
        )

    final_products = [
        product.model_copy(
            update={"image_url": image_urls.get(product.product_id, product.image_url)}
        )
        for product, _, _ in product_items
    ]

    logger.info("Step 4: Supabase 적재 시작...")
    sb_count = sb_loader.upsert_products(final_products)
    result["supabase_upserted"] = sb_count

    # Step 5: Pinecone 벡터 적재
    if embeddings:
        from app.pipeline.loader_pinecone import PineconeLoader

        logger.info("Step 5: Pinecone 적재 시작...")
        pc_loader = PineconeLoader(
            api_key=settings.pinecone_api_key,
            index_name=settings.pinecone_index,
        )

        pinecone_records = []
        for product, _, image_id in product_items:
            embedding = embeddings.get(image_id)
            if embedding is not None:
                record = pc_loader.build_pinecone_record(product, embedding)
                pinecone_records.append(record)

        pc_count = pc_loader.upsert_vectors(pinecone_records)
        result["pinecone_upserted"] = pc_count
    else:
        logger.info("Step 5: Pinecone 적재 스킵 (임베딩 없음)")

    # 요약 출력
    logger.info(
        "파이프라인 완료: Supabase %d건, Pinecone %d건",
        result["supabase_upserted"],
        result["pinecone_upserted"],
    )

    return result


def main() -> None:
    """CLI 엔트리포인트."""
    args = parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    try:
        run_pipeline(args)
    except FileNotFoundError as e:
        logger.error("파일을 찾을 수 없습니다: %s", e)
        sys.exit(1)
    except Exception as e:
        logger.error("파이프라인 실행 실패: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
