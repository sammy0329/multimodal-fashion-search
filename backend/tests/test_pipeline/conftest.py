"""파이프라인 테스트 공통 fixture."""

import json
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def single_label_path() -> Path:
    return FIXTURES_DIR / "sample_label_single.json"


@pytest.fixture
def multi_label_path() -> Path:
    return FIXTURES_DIR / "sample_label_multi.json"


@pytest.fixture
def resort_label_path() -> Path:
    return FIXTURES_DIR / "sample_label_resort.json"


@pytest.fixture
def single_label_data(single_label_path: Path) -> dict:
    with open(single_label_path, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def multi_label_data(multi_label_path: Path) -> dict:
    with open(multi_label_path, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def resort_label_data(resort_label_path: Path) -> dict:
    with open(resort_label_path, encoding="utf-8") as f:
        return json.load(f)
