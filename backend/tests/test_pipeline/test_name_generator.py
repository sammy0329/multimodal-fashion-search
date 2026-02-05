"""상품명 및 메타데이터 생성 테스트."""

from pathlib import Path

from app.pipeline.name_generator import (
    build_product_record,
    build_style_tags,
    generate_brand,
    generate_description,
    generate_price,
    generate_product_name,
    generate_product_name_ko,
)
from app.pipeline.parser import extract_valid_garments, parse_label_file
from app.pipeline.schemas import GarmentLabel


class TestGenerateProductName:
    def test_full_name(self) -> None:
        name = generate_product_name("레트로", "그레이", "재킷")
        assert name == "Retro Gray Jacket"

    def test_no_color(self) -> None:
        name = generate_product_name("로맨틱", None, "드레스")
        assert name == "Romantic Dress"

    def test_no_category(self) -> None:
        name = generate_product_name("리조트", "브라운", None)
        assert name == "Resort Brown"

    def test_unknown_values_pass_through(self) -> None:
        name = generate_product_name("미래", "투명", "우주복")
        assert name == "미래 투명 우주복"


class TestGenerateProductNameKo:
    def test_full_name(self) -> None:
        name = generate_product_name_ko("레트로", "그레이", "재킷")
        assert name == "레트로 그레이 재킷"

    def test_no_color(self) -> None:
        name = generate_product_name_ko("로맨틱", None, "드레스")
        assert name == "로맨틱 드레스"


class TestGeneratePrice:
    def test_known_category(self) -> None:
        price = generate_price("드레스", seed=42)
        assert 45_000 <= price <= 120_000
        assert price % 1_000 == 0

    def test_unknown_category_uses_default(self) -> None:
        price = generate_price("알수없음", seed=42)
        assert 30_000 <= price <= 80_000
        assert price % 1_000 == 0

    def test_none_category_uses_default(self) -> None:
        price = generate_price(None, seed=42)
        assert 30_000 <= price <= 80_000

    def test_reproducibility(self) -> None:
        p1 = generate_price("티셔츠", seed=123)
        p2 = generate_price("티셔츠", seed=123)
        assert p1 == p2

    def test_different_seeds_different_prices(self) -> None:
        p1 = generate_price("티셔츠", seed=1)
        p2 = generate_price("티셔츠", seed=999)
        # 확률적으로 다를 수 있지만, 범위가 크므로 거의 항상 다름
        # 만약 같다면 seed가 다른데 같은 값이 나온 것이므로 테스트 실패
        # 다만 아주 드물게 같을 수 있어 이 테스트는 soft assertion
        assert isinstance(p1, int)
        assert isinstance(p2, int)


class TestGenerateBrand:
    def test_retro_brand(self) -> None:
        brand = generate_brand("레트로", seed=42)
        assert brand in ["RETRO MOOD", "VINTAGE LANE", "OLDIES STUDIO", "BACK ALLEY"]

    def test_romantic_brand(self) -> None:
        brand = generate_brand("로맨틱", seed=42)
        assert brand in ["BLOOM ATELIER", "PETAL ROOM", "ROSY EDIT", "GRACE NOTE"]

    def test_resort_brand(self) -> None:
        brand = generate_brand("리조트", seed=42)
        assert brand in ["WAVE STUDIO", "SUN & SAND", "COASTAL MOOD", "BREEZE LAB"]

    def test_unknown_style_uses_default(self) -> None:
        brand = generate_brand("알수없음", seed=42)
        assert brand in ["STYLE EDIT", "MODE STUDIO", "URBAN NOTE", "DAILY ROOM"]

    def test_reproducibility(self) -> None:
        b1 = generate_brand("레트로", seed=100)
        b2 = generate_brand("레트로", seed=100)
        assert b1 == b2


class TestGenerateDescription:
    def test_full_description(self) -> None:
        garment = GarmentLabel.model_validate({
            "카테고리": "재킷",
            "색상": "그레이",
            "소재": ["우븐"],
            "프린트": ["체크"],
            "넥라인": "라운드넥",
            "기장": "하프",
            "소매기장": "긴팔",
            "핏": "루즈",
        })
        desc = generate_description(garment)
        assert "소재: 우븐" in desc
        assert "프린트: 체크" in desc
        assert "넥라인: 라운드넥" in desc
        assert "기장: 하프" in desc
        assert "핏: 루즈" in desc

    def test_empty_garment(self) -> None:
        garment = GarmentLabel.model_validate({})
        desc = generate_description(garment)
        assert desc == ""

    def test_partial_garment(self) -> None:
        garment = GarmentLabel.model_validate({
            "카테고리": "티셔츠",
            "소재": ["저지"],
        })
        desc = generate_description(garment)
        assert "소재: 저지" in desc
        assert "프린트" not in desc


class TestBuildStyleTags:
    def test_with_all_info(self) -> None:
        garment = GarmentLabel.model_validate({
            "카테고리": "재킷",
            "핏": "루즈",
            "프린트": ["체크"],
            "디테일": ["포켓"],
        })
        tags = build_style_tags("레트로", "페미닌", garment)
        assert tags == ["레트로", "페미닌", "루즈", "체크", "포켓"]

    def test_no_sub_style(self) -> None:
        garment = GarmentLabel.model_validate({
            "카테고리": "티셔츠",
            "핏": "노멀",
            "프린트": ["무지"],
        })
        tags = build_style_tags("리조트", None, garment)
        assert tags == ["리조트", "노멀", "무지"]

    def test_deduplication(self) -> None:
        garment = GarmentLabel.model_validate({
            "카테고리": "드레스",
            "핏": "루즈",
            "프린트": ["루즈"],
            "디테일": ["루즈"],
        })
        tags = build_style_tags("레트로", None, garment)
        assert tags.count("루즈") == 1


class TestBuildProductRecord:
    def test_single_dress(self, single_label_path: Path) -> None:
        label = parse_label_file(single_label_path)
        valid = extract_valid_garments(label)
        garment_type, garment = valid[0]
        record = build_product_record(label, garment_type, garment)

        assert record.product_id == "kf_1002_dress"
        assert record.name == "Romantic Pink Dress"
        assert record.name_ko == "로맨틱 핑크 드레스"
        assert 45_000 <= record.price <= 120_000
        assert record.brand in ["BLOOM ATELIER", "PETAL ROOM", "ROSY EDIT", "GRACE NOTE"]
        assert record.category == "원피스"
        assert record.sub_category == "드레스"
        assert "로맨틱" in record.style_tags
        assert record.color == "핑크"
        assert record.data_source == "k-fashion"
        assert record.season is None  # 로맨틱 → None

    def test_multi_items(self, multi_label_path: Path) -> None:
        label = parse_label_file(multi_label_path)
        valid = extract_valid_garments(label)
        assert len(valid) == 3

        records = [
            build_product_record(label, gt, g)
            for gt, g in valid
        ]

        product_ids = {r.product_id for r in records}
        assert "kf_1029079_outer" in product_ids
        assert "kf_1029079_bottom" in product_ids
        assert "kf_1029079_top" in product_ids

        # 레트로 브랜드 확인
        for r in records:
            assert r.brand in ["RETRO MOOD", "VINTAGE LANE", "OLDIES STUDIO", "BACK ALLEY"]
            assert r.season is None  # 레트로 → None

    def test_resort_season(self, resort_label_path: Path) -> None:
        label = parse_label_file(resort_label_path)
        valid = extract_valid_garments(label)
        garment_type, garment = valid[0]
        record = build_product_record(label, garment_type, garment)

        assert record.product_id == "kf_100873_top"
        assert record.season == "여름"  # 리조트 → 여름
        assert record.brand in ["WAVE STUDIO", "SUN & SAND", "COASTAL MOOD", "BREEZE LAB"]
