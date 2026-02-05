"""파이프라인 스키마 유닛 테스트."""

import pytest

from app.pipeline.constants import (
    BRAND_MAP,
    CATEGORY_ROMANIZE,
    COLOR_ROMANIZE,
    DEFAULT_PRICE_RANGE,
    GARMENT_TYPES,
    PRICE_RANGE,
    STYLE_ROMANIZE,
    STYLE_SEASON_MAP,
)
from app.pipeline.schemas import (
    AIHubLabel,
    GarmentLabel,
    PineconeRecord,
    ProductRecord,
    StyleLabel,
)


class TestGarmentLabel:
    def test_parse_full_garment(self) -> None:
        data = {
            "카테고리": "재킷",
            "색상": "그레이",
            "서브색상": "화이트",
            "소매기장": "긴팔",
            "기장": "하프",
            "넥라인": None,
            "옷깃": "테일러드칼라",
            "핏": "루즈",
            "소재": ["우븐"],
            "프린트": ["체크"],
            "디테일": ["포켓"],
        }
        label = GarmentLabel.model_validate(data)
        assert label.category == "재킷"
        assert label.color == "그레이"
        assert label.fit == "루즈"
        assert label.material == ["우븐"]
        assert not label.is_empty()

    def test_empty_garment(self) -> None:
        label = GarmentLabel.model_validate({})
        assert label.is_empty()
        assert label.category is None
        assert label.material == []
        assert label.prints == []
        assert label.detail == []

    def test_partial_garment(self) -> None:
        data = {
            "색상": "브라운",
            "카테고리": "티셔츠",
            "소재": ["저지"],
            "프린트": ["무지"],
        }
        label = GarmentLabel.model_validate(data)
        assert not label.is_empty()
        assert label.color == "브라운"
        assert label.sleeve_length is None
        assert label.detail == []


class TestStyleLabel:
    def test_with_sub_style(self) -> None:
        data = {"스타일": "로맨틱", "서브스타일": "리조트"}
        label = StyleLabel.model_validate(data)
        assert label.style == "로맨틱"
        assert label.sub_style == "리조트"

    def test_without_sub_style(self) -> None:
        data = {"스타일": "레트로"}
        label = StyleLabel.model_validate(data)
        assert label.style == "레트로"
        assert label.sub_style is None


class TestAIHubLabel:
    def test_create(self) -> None:
        style = StyleLabel.model_validate({"스타일": "레트로"})
        garments = {
            "상의": GarmentLabel.model_validate({"카테고리": "티셔츠", "색상": "화이트"}),
            "하의": GarmentLabel.model_validate({}),
        }
        label = AIHubLabel(
            image_id=1029079,
            image_filename="test.jpg",
            style=style,
            garments=garments,
        )
        assert label.image_id == 1029079
        assert not label.garments["상의"].is_empty()
        assert label.garments["하의"].is_empty()


class TestProductRecord:
    def test_to_supabase_dict(self) -> None:
        record = ProductRecord(
            product_id="kf_1002_dress",
            name="Romantic Pink Dress",
            name_ko="로맨틱 핑크 드레스",
            price=67_000,
            brand="BLOOM ATELIER",
            category="원피스",
            sub_category="드레스",
            style_tags=["로맨틱", "리조트"],
            color="핑크",
            image_url="https://example.com/img.jpg",
            season=None,
        )
        d = record.to_supabase_dict()
        assert d["product_id"] == "kf_1002_dress"
        assert d["price"] == 67_000
        assert d["is_soldout"] is False
        assert d["data_source"] == "k-fashion"
        assert isinstance(d["style_tags"], list)

    def test_price_validation(self) -> None:
        with pytest.raises(Exception):
            ProductRecord(
                product_id="test",
                name="test",
                name_ko="테스트",
                price=-1,
                brand="brand",
                category="상의",
                sub_category="티셔츠",
            )


class TestPineconeRecord:
    def test_to_pinecone_dict(self) -> None:
        record = PineconeRecord(
            id="product_kf_1002_dress",
            values=[0.1] * 512,
            metadata={"category": "원피스", "price": 67_000},
        )
        d = record.to_pinecone_dict()
        assert d["id"] == "product_kf_1002_dress"
        assert len(d["values"]) == 512
        assert d["metadata"]["category"] == "원피스"


class TestConstants:
    def test_garment_types_coverage(self) -> None:
        assert set(GARMENT_TYPES.keys()) == {"상의", "하의", "아우터", "원피스"}

    def test_price_range_values(self) -> None:
        for category, (low, high) in PRICE_RANGE.items():
            assert low > 0, f"{category}: 최소 가격은 0보다 커야 한다"
            assert high > low, f"{category}: 최대 가격은 최소보다 커야 한다"

    def test_default_price_range(self) -> None:
        low, high = DEFAULT_PRICE_RANGE
        assert low > 0
        assert high > low

    def test_brand_map_all_styles(self) -> None:
        for style in ["레트로", "로맨틱", "리조트"]:
            assert style in BRAND_MAP
            assert len(BRAND_MAP[style]) == 4

    def test_style_season_map(self) -> None:
        assert STYLE_SEASON_MAP["리조트"] == "여름"
        assert STYLE_SEASON_MAP["레트로"] is None
        assert STYLE_SEASON_MAP["로맨틱"] is None

    def test_color_romanize_coverage(self) -> None:
        assert "블랙" in COLOR_ROMANIZE
        assert "화이트" in COLOR_ROMANIZE
        assert COLOR_ROMANIZE["핑크"] == "Pink"

    def test_category_romanize_coverage(self) -> None:
        assert "티셔츠" in CATEGORY_ROMANIZE
        assert CATEGORY_ROMANIZE["드레스"] == "Dress"

    def test_style_romanize_coverage(self) -> None:
        for style in BRAND_MAP:
            assert style in STYLE_ROMANIZE
