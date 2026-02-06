"""LLM 프롬프트 템플릿 빌더.

한국어 패션 AI 스타일리스트 페르소나 기반 추천 코멘트 프롬프트를 구성한다.
"""

from typing import Any

SYSTEM_PROMPT = """당신은 '스타일 매처'의 AI 패션 스타일리스트입니다.
사용자가 찾고 있는 스타일에 맞는 상품을 추천하고, 왜 이 상품들이 잘 어울리는지 설명합니다.

## 역할
- 친근하고 전문적인 패션 어드바이저
- 한국 패션 트렌드에 정통
- 실용적인 스타일링 팁 제공

## 응답 규칙
1. 자연스러운 한국어로 작성
2. 각 상품의 스타일 특징을 구체적으로 설명
3. 어울리는 코디 조합 제안 (예: "와이드 데님과 잘 어울려요")
4. 착용 상황(TPO) 추천 포함
5. 과도한 수식어 자제, 실질적 조언 위주
6. 500자 이내로 간결하게 작성

## 중요
- 제공된 상품 정보에 있는 내용만 언급하세요
- 브랜드, 소재, 가격 등은 정확히 데이터대로 말하세요
- 데이터에 없는 정보는 추측하지 마세요"""


def build_product_context(products: list[dict[str, Any]]) -> str:
    """상품 목록을 LLM 입력용 텍스트로 변환한다.

    Args:
        products: Supabase에서 조회한 상품 딕셔너리 리스트.

    Returns:
        상품 정보 텍스트 블록.
    """
    if not products:
        return ""

    lines: list[str] = []

    for i, product in enumerate(products, 1):
        name = product.get("name_ko") or product.get("name", "알 수 없음")
        brand = product.get("brand", "알 수 없음")
        category = product.get("category", "")
        sub_category = product.get("sub_category", "")
        price = product.get("price", 0)
        color = product.get("color", "")
        style_tags = product.get("style_tags") or []
        material = product.get("material", "")
        season = product.get("season", "")
        description = product.get("description", "")

        parts = [f"[상품 {i}]"]
        parts.append(f"- 이름: {name}")
        parts.append(f"- 브랜드: {brand}")

        if category:
            category_text = f"{category}/{sub_category}" if sub_category else category
            parts.append(f"- 카테고리: {category_text}")

        parts.append(f"- 가격: {price:,}원")

        if color:
            parts.append(f"- 색상: {color}")

        if style_tags:
            parts.append(f"- 스타일: {', '.join(style_tags)}")

        if material:
            parts.append(f"- 소재: {material}")

        if season:
            parts.append(f"- 시즌: {season}")

        if description:
            truncated = description[:100] + "..." if len(description) > 100 else description
            parts.append(f"- 설명: {truncated}")

        lines.append("\n".join(parts))

    return "\n\n".join(lines)


def build_user_message(
    product_context: str, user_query: str | None = None
) -> str:
    """사용자 메시지를 구성한다.

    Args:
        product_context: build_product_context()로 생성한 텍스트.
        user_query: 원래 검색 쿼리 (선택).

    Returns:
        완성된 사용자 메시지.
    """
    parts: list[str] = []

    if user_query:
        parts.append(f"사용자가 '{user_query}'을(를) 검색하여 아래 상품들을 찾았습니다.")
    else:
        parts.append("아래 상품들에 대한 스타일링 추천을 해주세요.")

    parts.append("")
    parts.append(product_context)
    parts.append("")
    parts.append("이 상품들에 대한 스타일 추천 코멘트를 작성해주세요.")

    return "\n".join(parts)
