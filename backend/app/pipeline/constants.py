"""데이터 파이프라인 상수 정의.

AI Hub K-Fashion 데이터의 의류 타입, 가격 범위, 브랜드, 색상 로마자 변환 등을 관리한다.
"""

# 의류 타입별 garment suffix 매핑
GARMENT_TYPES: dict[str, str] = {
    "상의": "top",
    "하의": "bottom",
    "아우터": "outer",
    "원피스": "dress",
}

# 카테고리별 가격 범위 (원)
PRICE_RANGE: dict[str, tuple[int, int]] = {
    "티셔츠": (25_000, 65_000),
    "탑": (25_000, 65_000),
    "블라우스": (35_000, 85_000),
    "셔츠": (35_000, 85_000),
    "니트웨어": (40_000, 95_000),
    "스커트": (30_000, 85_000),
    "팬츠": (35_000, 95_000),
    "청바지": (35_000, 95_000),
    "드레스": (45_000, 120_000),
    "점프수트": (45_000, 120_000),
    "재킷": (70_000, 180_000),
    "코트": (70_000, 180_000),
    "점퍼": (70_000, 180_000),
    "패딩": (70_000, 180_000),
    "가디건": (45_000, 110_000),
    "베스트": (45_000, 110_000),
}

DEFAULT_PRICE_RANGE: tuple[int, int] = (30_000, 80_000)

# 스타일별 가상 브랜드
BRAND_MAP: dict[str, list[str]] = {
    "레트로": ["RETRO MOOD", "VINTAGE LANE", "OLDIES STUDIO", "BACK ALLEY"],
    "로맨틱": ["BLOOM ATELIER", "PETAL ROOM", "ROSY EDIT", "GRACE NOTE"],
    "리조트": ["WAVE STUDIO", "SUN & SAND", "COASTAL MOOD", "BREEZE LAB"],
}

DEFAULT_BRANDS: list[str] = ["STYLE EDIT", "MODE STUDIO", "URBAN NOTE", "DAILY ROOM"]

# 스타일 → 시즌 매핑
STYLE_SEASON_MAP: dict[str, str | None] = {
    "레트로": None,
    "로맨틱": None,
    "리조트": "여름",
}

# 한국어 색상 → 로마자 변환
COLOR_ROMANIZE: dict[str, str] = {
    "블랙": "Black",
    "화이트": "White",
    "그레이": "Gray",
    "레드": "Red",
    "핑크": "Pink",
    "오렌지": "Orange",
    "옐로우": "Yellow",
    "그린": "Green",
    "블루": "Blue",
    "네이비": "Navy",
    "퍼플": "Purple",
    "베이지": "Beige",
    "브라운": "Brown",
    "카키": "Khaki",
    "와인": "Wine",
    "라벤더": "Lavender",
    "스카이블루": "Sky Blue",
    "민트": "Mint",
    "골드": "Gold",
    "실버": "Silver",
    "아이보리": "Ivory",
    "카멜": "Camel",
    "연청": "Light Blue",
    "중청": "Mid Blue",
    "진청": "Dark Blue",
    "흑청": "Black Blue",
}

# 한국어 카테고리 → 로마자 변환
CATEGORY_ROMANIZE: dict[str, str] = {
    "티셔츠": "T-shirt",
    "탑": "Top",
    "블라우스": "Blouse",
    "셔츠": "Shirt",
    "니트웨어": "Knitwear",
    "스커트": "Skirt",
    "팬츠": "Pants",
    "청바지": "Jeans",
    "드레스": "Dress",
    "점프수트": "Jumpsuit",
    "재킷": "Jacket",
    "코트": "Coat",
    "점퍼": "Jumper",
    "패딩": "Padded Jacket",
    "가디건": "Cardigan",
    "베스트": "Vest",
}

# 한국어 스타일 → 로마자 변환
STYLE_ROMANIZE: dict[str, str] = {
    "레트로": "Retro",
    "로맨틱": "Romantic",
    "리조트": "Resort",
    "매니시": "Mannish",
    "모던": "Modern",
    "밀리터리": "Military",
    "소피스트케이티드": "Sophisticated",
    "스포티": "Sporty",
    "아방가르드": "Avant-garde",
    "젠더리스": "Genderless",
    "컨트리": "Country",
    "클래식": "Classic",
    "톰보이": "Tomboy",
    "펑크": "Punk",
    "페미닌": "Feminine",
    "프레피": "Preppy",
    "히피": "Hippie",
    "힙합": "Hip-hop",
}

# 가격 반올림 단위
PRICE_ROUND_UNIT: int = 1_000
