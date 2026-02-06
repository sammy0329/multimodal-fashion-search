"""AI Hub K-Fashion JSON 라벨 파서.

JSON 라벨 파일을 파싱하여 AIHubLabel 객체로 변환하고,
이미지 디렉토리를 스캔하여 라벨-이미지 쌍 목록을 반환한다.
"""

import json
import logging
from pathlib import Path

from app.pipeline.constants import GARMENT_TYPES
from app.pipeline.schemas import AIHubLabel, GarmentLabel, StyleLabel

logger = logging.getLogger(__name__)


def parse_label_file(path: Path) -> AIHubLabel | None:
    """JSON 라벨 파일 하나를 파싱하여 AIHubLabel을 반환한다.

    Args:
        path: JSON 파일 경로

    Returns:
        파싱된 AIHubLabel, 또는 유효하지 않은 데이터면 None

    Raises:
        FileNotFoundError: 파일이 없을 때
    """
    try:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)

        image_info = raw["이미지 정보"]
        labeling = raw["데이터셋 정보"]["데이터셋 상세설명"]["라벨링"]

        style_list = labeling.get("스타일", [])
        if not style_list or not style_list[0].get("스타일"):
            logger.debug("스타일 정보 없음: %s", path.name)
            return None

        style_data = style_list[0]
        style = StyleLabel.model_validate(style_data)

        garments: dict[str, GarmentLabel] = {}
        for garment_type in GARMENT_TYPES:
            items = labeling.get(garment_type, [{}])
            garment_data = items[0] if items else {}
            garments[garment_type] = GarmentLabel.model_validate(garment_data)

        return AIHubLabel(
            image_id=image_info["이미지 식별자"],
            image_filename=image_info["이미지 파일명"],
            style=style,
            garments=garments,
        )
    except (KeyError, ValueError) as e:
        logger.warning("라벨 파싱 실패 %s: %s", path.name, e)
        return None


def extract_valid_garments(label: AIHubLabel) -> list[tuple[str, GarmentLabel]]:
    """빈 슬롯을 제외한 유효 의류 아이템 목록을 반환한다.

    Args:
        label: 파싱된 AIHubLabel

    Returns:
        (garment_type_key, GarmentLabel) 튜플 리스트
    """
    return [
        (garment_type, garment)
        for garment_type, garment in label.garments.items()
        if not garment.is_empty()
    ]


def scan_data_directory(
    data_dir: Path,
    limit_per_style: int | None = None,
) -> list[tuple[Path, Path, str]]:
    """데이터 디렉토리를 스캔하여 (라벨 파일, 이미지 파일, 스타일) 튜플 목록을 반환한다.

    디렉토리 구조:
        data_dir/
        ├── 라벨링데이터/{스타일}/*.json
        └── 원천데이터/{스타일}/*.jpg

    Args:
        data_dir: 샘플 데이터 루트 디렉토리
        limit_per_style: 스타일당 최대 샘플 수 (None이면 제한 없음)

    Returns:
        (label_path, image_path, style_name) 튜플 리스트
    """
    label_root = data_dir / "라벨링데이터"
    image_root = data_dir / "원천데이터"

    if not label_root.exists():
        raise FileNotFoundError(f"라벨링데이터 디렉토리를 찾을 수 없습니다: {label_root}")

    results: list[tuple[Path, Path, str]] = []

    for style_dir in sorted(label_root.iterdir()):
        if not style_dir.is_dir():
            continue

        style_name = style_dir.name
        image_dir = image_root / style_name
        style_count = 0

        for label_path in sorted(style_dir.glob("*.json")):
            # 스타일당 제한이 있고 도달했으면 다음 스타일로
            if limit_per_style is not None and style_count >= limit_per_style:
                break

            image_id = label_path.stem
            image_candidates = list(image_dir.glob(f"{image_id}.*"))
            jpg_candidates = [
                p for p in image_candidates if p.suffix.lower() in (".jpg", ".jpeg", ".png")
            ]

            if not jpg_candidates:
                logger.warning("이미지 파일 없음: %s (스타일: %s)", image_id, style_name)
                continue

            results.append((label_path, jpg_candidates[0], style_name))
            style_count += 1

        if limit_per_style is not None:
            logger.debug("스타일 '%s': %d개 샘플링", style_name, style_count)

    logger.info("스캔 완료: %d개 라벨-이미지 쌍", len(results))
    return results
