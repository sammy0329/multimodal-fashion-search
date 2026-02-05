"""상품명 및 메타데이터 생성 모듈.

AI Hub 라벨 데이터로부터 상품명(한국어/영어), 가격, 브랜드, 설명 등을 생성한다.
"""

import random

from app.pipeline.constants import (
    BRAND_MAP,
    CATEGORY_ROMANIZE,
    COLOR_ROMANIZE,
    DEFAULT_BRANDS,
    DEFAULT_PRICE_RANGE,
    GARMENT_TYPES,
    PRICE_RANGE,
    PRICE_ROUND_UNIT,
    STYLE_ROMANIZE,
    STYLE_SEASON_MAP,
)
from app.pipeline.schemas import AIHubLabel, GarmentLabel, ProductRecord


def generate_product_name(
    style: str,
    color: str | None,
    sub_category: str | None,
) -> str:
    """영문 상품명을 생성한다.

    Args:
        style: 스타일 (한국어)
        color: 색상 (한국어)
        sub_category: 세부 카테고리 (한국어)

    Returns:
        영문 상품명 (예: "Retro Gray Jacket")
    """
    parts: list[str] = []
    parts.append(STYLE_ROMANIZE.get(style, style))
    if color:
        parts.append(COLOR_ROMANIZE.get(color, color))
    if sub_category:
        parts.append(CATEGORY_ROMANIZE.get(sub_category, sub_category))
    return " ".join(parts)


def generate_product_name_ko(
    style: str,
    color: str | None,
    sub_category: str | None,
) -> str:
    """한국어 상품명을 생성한다.

    Args:
        style: 스타일 (한국어)
        color: 색상 (한국어)
        sub_category: 세부 카테고리 (한국어)

    Returns:
        한국어 상품명 (예: "레트로 그레이 재킷")
    """
    parts: list[str] = [style]
    if color:
        parts.append(color)
    if sub_category:
        parts.append(sub_category)
    return " ".join(parts)


def generate_price(sub_category: str | None, seed: int) -> int:
    """카테고리별 가격 범위 내에서 가격을 생성한다.

    Args:
        sub_category: 세부 카테고리 (한국어)
        seed: 랜덤 시드 (재현성 보장)

    Returns:
        1,000원 단위로 반올림된 가격
    """
    rng = random.Random(seed)
    price_range = PRICE_RANGE.get(sub_category or "", DEFAULT_PRICE_RANGE)
    raw_price = rng.randint(price_range[0], price_range[1])
    return round(raw_price / PRICE_ROUND_UNIT) * PRICE_ROUND_UNIT


def generate_brand(style: str, seed: int) -> str:
    """스타일별 가상 브랜드를 선택한다.

    Args:
        style: 스타일 (한국어)
        seed: 랜덤 시드

    Returns:
        브랜드명
    """
    rng = random.Random(seed)
    brands = BRAND_MAP.get(style, DEFAULT_BRANDS)
    return rng.choice(brands)


def generate_description(garment: GarmentLabel) -> str:
    """의류 라벨 정보로 설명 문자열을 생성한다.

    Args:
        garment: 의류 라벨

    Returns:
        설명 문자열 (예: "소재: 우븐 / 프린트: 체크 / 넥라인: 라운드넥 / 기장: 하프")
    """
    parts: list[str] = []
    if garment.material:
        parts.append(f"소재: {', '.join(garment.material)}")
    if garment.prints:
        parts.append(f"프린트: {', '.join(garment.prints)}")
    if garment.neckline:
        parts.append(f"넥라인: {garment.neckline}")
    if garment.collar:
        parts.append(f"옷깃: {garment.collar}")
    if garment.length:
        parts.append(f"기장: {garment.length}")
    if garment.sleeve_length:
        parts.append(f"소매: {garment.sleeve_length}")
    if garment.fit:
        parts.append(f"핏: {garment.fit}")
    return " / ".join(parts)


def build_style_tags(
    style: str,
    sub_style: str | None,
    garment: GarmentLabel,
) -> list[str]:
    """스타일 태그 리스트를 구성한다.

    Args:
        style: 메인 스타일
        sub_style: 서브 스타일
        garment: 의류 라벨

    Returns:
        중복 제거된 스타일 태그 리스트
    """
    tags: list[str] = [style]
    if sub_style:
        tags.append(sub_style)
    if garment.fit:
        tags.append(garment.fit)
    tags.extend(garment.prints)
    tags.extend(garment.detail)
    # 중복 제거하면서 순서 유지
    seen: set[str] = set()
    unique_tags: list[str] = []
    for tag in tags:
        if tag not in seen:
            seen.add(tag)
            unique_tags.append(tag)
    return unique_tags


def build_product_record(
    label: AIHubLabel,
    garment_type: str,
    garment: GarmentLabel,
) -> ProductRecord:
    """AIHubLabel + GarmentLabel로 ProductRecord를 생성한다.

    Args:
        label: AI Hub 라벨 전체
        garment_type: 의류 타입 키 (상의/하의/아우터/원피스)
        garment: 해당 의류 라벨

    Returns:
        ProductRecord
    """
    suffix = GARMENT_TYPES[garment_type]
    product_id = f"kf_{label.image_id}_{suffix}"

    style = label.style.style
    sub_style = label.style.sub_style

    # seed = image_id * 100 + garment type hash로 재현성 보장
    seed = label.image_id * 100 + hash(suffix) % 100

    return ProductRecord(
        product_id=product_id,
        name=generate_product_name(style, garment.color, garment.category),
        name_ko=generate_product_name_ko(style, garment.color, garment.category),
        price=generate_price(garment.category, seed),
        brand=generate_brand(style, seed),
        category=garment_type,
        sub_category=garment.category or "",
        style_tags=build_style_tags(style, sub_style, garment),
        color=garment.color,
        description=generate_description(garment),
        material=", ".join(garment.material) if garment.material else None,
        season=STYLE_SEASON_MAP.get(style),
    )
