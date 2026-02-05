"""AI Hub JSON 라벨 파서 테스트."""

import tempfile
from pathlib import Path

import pytest

from app.pipeline.parser import (
    extract_valid_garments,
    parse_label_file,
    scan_data_directory,
)


class TestParseLabelFile:
    def test_single_item(self, single_label_path: Path) -> None:
        label = parse_label_file(single_label_path)
        assert label.image_id == 1002
        assert label.image_filename == "test_dress.jpg"
        assert label.style.style == "로맨틱"
        assert label.style.sub_style == "리조트"
        assert not label.garments["원피스"].is_empty()
        assert label.garments["원피스"].category == "드레스"
        assert label.garments["상의"].is_empty()
        assert label.garments["하의"].is_empty()
        assert label.garments["아우터"].is_empty()

    def test_multi_item(self, multi_label_path: Path) -> None:
        label = parse_label_file(multi_label_path)
        assert label.image_id == 1029079
        assert label.style.style == "레트로"
        assert label.style.sub_style is None
        assert not label.garments["아우터"].is_empty()
        assert not label.garments["하의"].is_empty()
        assert not label.garments["상의"].is_empty()
        assert label.garments["원피스"].is_empty()

    def test_multi_item_details(self, multi_label_path: Path) -> None:
        label = parse_label_file(multi_label_path)
        outer = label.garments["아우터"]
        assert outer.category == "재킷"
        assert outer.color == "그레이"
        assert outer.fit == "루즈"
        assert outer.material == ["우븐"]
        assert outer.prints == ["체크"]
        assert outer.detail == ["포켓"]

    def test_resort_item(self, resort_label_path: Path) -> None:
        label = parse_label_file(resort_label_path)
        assert label.style.style == "리조트"
        top = label.garments["상의"]
        assert top.category == "티셔츠"
        assert top.color == "브라운"
        assert top.neckline == "보트넥"

    def test_file_not_found(self) -> None:
        with pytest.raises(FileNotFoundError):
            parse_label_file(Path("/nonexistent/file.json"))


class TestExtractValidGarments:
    def test_single_item_extracts_one(self, single_label_path: Path) -> None:
        label = parse_label_file(single_label_path)
        valid = extract_valid_garments(label)
        assert len(valid) == 1
        garment_type, garment = valid[0]
        assert garment_type == "원피스"
        assert garment.category == "드레스"

    def test_multi_item_extracts_three(self, multi_label_path: Path) -> None:
        label = parse_label_file(multi_label_path)
        valid = extract_valid_garments(label)
        assert len(valid) == 3
        types = {t for t, _ in valid}
        assert types == {"아우터", "하의", "상의"}

    def test_resort_extracts_one(self, resort_label_path: Path) -> None:
        label = parse_label_file(resort_label_path)
        valid = extract_valid_garments(label)
        assert len(valid) == 1
        assert valid[0][0] == "상의"


class TestScanDataDirectory:
    def test_scan_with_matching_images(self, tmp_path: Path) -> None:
        label_dir = tmp_path / "라벨링데이터" / "레트로"
        image_dir = tmp_path / "원천데이터" / "레트로"
        label_dir.mkdir(parents=True)
        image_dir.mkdir(parents=True)

        (label_dir / "123.json").write_text("{}", encoding="utf-8")
        (image_dir / "123.jpg").write_text("fake image")

        (label_dir / "456.json").write_text("{}", encoding="utf-8")
        (image_dir / "456.jpg").write_text("fake image")

        results = scan_data_directory(tmp_path)
        assert len(results) == 2
        assert results[0][2] == "레트로"

    def test_scan_skips_missing_images(self, tmp_path: Path) -> None:
        label_dir = tmp_path / "라벨링데이터" / "로맨틱"
        image_dir = tmp_path / "원천데이터" / "로맨틱"
        label_dir.mkdir(parents=True)
        image_dir.mkdir(parents=True)

        (label_dir / "789.json").write_text("{}", encoding="utf-8")
        # 이미지 파일 없음

        results = scan_data_directory(tmp_path)
        assert len(results) == 0

    def test_scan_missing_directory(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            scan_data_directory(tmp_path / "nonexistent")

    def test_scan_multiple_styles(self, tmp_path: Path) -> None:
        for style in ["레트로", "로맨틱"]:
            label_dir = tmp_path / "라벨링데이터" / style
            image_dir = tmp_path / "원천데이터" / style
            label_dir.mkdir(parents=True)
            image_dir.mkdir(parents=True)
            (label_dir / "100.json").write_text("{}", encoding="utf-8")
            (image_dir / "100.jpg").write_text("fake")

        results = scan_data_directory(tmp_path)
        assert len(results) == 2
        styles = {r[2] for r in results}
        assert styles == {"레트로", "로맨틱"}
