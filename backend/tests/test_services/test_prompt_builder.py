"""프롬프트 빌더 유닛 테스트."""

import pytest

from app.services.prompt import (
    SYSTEM_PROMPT,
    build_product_context,
    build_user_message,
)


class TestSystemPrompt:
    """시스템 프롬프트 테스트."""

    def test_system_prompt_is_nonempty_string(self) -> None:
        """시스템 프롬프트가 비어있지 않은 문자열이다."""
        assert isinstance(SYSTEM_PROMPT, str)
        assert len(SYSTEM_PROMPT) > 100

    def test_system_prompt_contains_role(self) -> None:
        """시스템 프롬프트에 역할이 정의되어 있다."""
        assert "스타일리스트" in SYSTEM_PROMPT
        assert "패션" in SYSTEM_PROMPT

    def test_system_prompt_contains_rules(self) -> None:
        """시스템 프롬프트에 응답 규칙이 포함되어 있다."""
        assert "응답 규칙" in SYSTEM_PROMPT
        assert "500자" in SYSTEM_PROMPT


class TestBuildProductContext:
    """build_product_context() 테스트."""

    def test_single_product_all_fields(self) -> None:
        """모든 필드가 있는 단일 상품을 렌더링한다."""
        products = [
            {
                "name": "Oxford Shirt",
                "name_ko": "옥스포드 셔츠",
                "brand": "브랜드A",
                "category": "상의",
                "sub_category": "셔츠",
                "price": 45000,
                "color": "화이트",
                "style_tags": ["캐주얼", "오버핏"],
                "material": "면",
                "season": "봄/가을",
                "description": "편안한 착용감의 옥스포드 셔츠",
            }
        ]
        result = build_product_context(products)

        assert "[상품 1]" in result
        assert "옥스포드 셔츠" in result
        assert "브랜드A" in result
        assert "상의/셔츠" in result
        assert "45,000원" in result
        assert "화이트" in result
        assert "캐주얼, 오버핏" in result
        assert "면" in result
        assert "봄/가을" in result
        assert "편안한 착용감" in result

    def test_multiple_products_numbered(self) -> None:
        """여러 상품이 번호로 구분된다."""
        products = [
            {"name": "상품1", "price": 10000},
            {"name": "상품2", "price": 20000},
            {"name": "상품3", "price": 30000},
        ]
        result = build_product_context(products)

        assert "[상품 1]" in result
        assert "[상품 2]" in result
        assert "[상품 3]" in result
        assert "상품1" in result
        assert "상품2" in result
        assert "상품3" in result

    def test_missing_optional_fields(self) -> None:
        """선택 필드가 없어도 렌더링된다."""
        products = [{"name": "기본 상품", "price": 15000}]
        result = build_product_context(products)

        assert "[상품 1]" in result
        assert "기본 상품" in result
        assert "15,000원" in result
        assert "색상" not in result
        assert "스타일" not in result

    def test_prefers_name_ko_over_name(self) -> None:
        """name_ko가 있으면 name보다 우선한다."""
        products = [
            {"name": "English Name", "name_ko": "한국어 이름", "price": 10000}
        ]
        result = build_product_context(products)

        assert "한국어 이름" in result
        assert "English Name" not in result

    def test_falls_back_to_name(self) -> None:
        """name_ko가 없으면 name을 사용한다."""
        products = [{"name": "English Name", "price": 10000}]
        result = build_product_context(products)

        assert "English Name" in result

    def test_empty_list_returns_empty_string(self) -> None:
        """빈 리스트는 빈 문자열을 반환한다."""
        result = build_product_context([])
        assert result == ""

    def test_long_description_truncated(self) -> None:
        """긴 설명은 100자로 잘린다."""
        long_desc = "a" * 150
        products = [{"name": "상품", "price": 10000, "description": long_desc}]
        result = build_product_context(products)

        assert "a" * 100 + "..." in result
        assert "a" * 150 not in result

    def test_category_without_subcategory(self) -> None:
        """서브카테고리가 없으면 카테고리만 표시한다."""
        products = [{"name": "상품", "price": 10000, "category": "상의"}]
        result = build_product_context(products)

        assert "카테고리: 상의" in result
        assert "상의/" not in result

    def test_empty_style_tags_not_shown(self) -> None:
        """빈 스타일 태그 리스트는 표시하지 않는다."""
        products = [{"name": "상품", "price": 10000, "style_tags": []}]
        result = build_product_context(products)

        assert "스타일" not in result


class TestBuildUserMessage:
    """build_user_message() 테스트."""

    def test_with_user_query(self) -> None:
        """사용자 쿼리가 있으면 포함된다."""
        context = "[상품 1]\n- 이름: 테스트 상품"
        result = build_user_message(context, user_query="오버핏 셔츠")

        assert "오버핏 셔츠" in result
        assert "검색하여" in result
        assert "테스트 상품" in result
        assert "스타일 추천 코멘트" in result

    def test_without_user_query(self) -> None:
        """사용자 쿼리가 없으면 일반 문구를 사용한다."""
        context = "[상품 1]\n- 이름: 테스트 상품"
        result = build_user_message(context, user_query=None)

        assert "스타일링 추천을 해주세요" in result
        assert "검색하여" not in result

    def test_includes_product_context(self) -> None:
        """상품 컨텍스트가 포함된다."""
        context = "상품 정보 텍스트"
        result = build_user_message(context, user_query="쿼리")

        assert "상품 정보 텍스트" in result

    def test_ends_with_request(self) -> None:
        """마지막에 요청 문구가 있다."""
        result = build_user_message("컨텍스트", user_query="쿼리")

        assert result.endswith("이 상품들에 대한 스타일 추천 코멘트를 작성해주세요.")
