"""데이터 파이프라인 Pydantic 스키마.

AI Hub JSON 라벨 파싱 결과와 Supabase/Pinecone 적재용 레코드를 정의한다.
"""

from pydantic import BaseModel, Field


class StyleLabel(BaseModel):
    """스타일 라벨."""

    style: str = Field(alias="스타일")
    sub_style: str | None = Field(default=None, alias="서브스타일")


class GarmentLabel(BaseModel):
    """개별 의류 아이템 라벨."""

    category: str | None = Field(default=None, alias="카테고리")
    color: str | None = Field(default=None, alias="색상")
    sub_color: str | None = Field(default=None, alias="서브색상")
    sleeve_length: str | None = Field(default=None, alias="소매기장")
    length: str | None = Field(default=None, alias="기장")
    neckline: str | None = Field(default=None, alias="넥라인")
    collar: str | None = Field(default=None, alias="옷깃")
    fit: str | None = Field(default=None, alias="핏")
    material: list[str] = Field(default_factory=list, alias="소재")
    prints: list[str] = Field(default_factory=list, alias="프린트")
    detail: list[str] = Field(default_factory=list, alias="디테일")

    def is_empty(self) -> bool:
        """빈 슬롯인지 판별한다 (카테고리가 없으면 빈 아이템)."""
        return self.category is None


class AIHubLabel(BaseModel):
    """AI Hub JSON 파일 하나의 파싱 결과."""

    image_id: int
    image_filename: str
    style: StyleLabel
    garments: dict[str, GarmentLabel] = Field(
        description="garment_type(상의/하의/아우터/원피스) → GarmentLabel"
    )


class ProductRecord(BaseModel):
    """Supabase products 테이블에 적재할 레코드."""

    product_id: str
    name: str
    name_ko: str
    price: int = Field(ge=0)
    brand: str
    category: str
    sub_category: str
    style_tags: list[str] = Field(default_factory=list)
    color: str | None = None
    image_url: str = ""
    description: str = ""
    material: str | None = None
    season: str | None = None
    data_source: str = "k-fashion"
    is_soldout: bool = False

    def to_supabase_dict(self) -> dict:
        """Supabase upsert용 딕셔너리를 반환한다."""
        return self.model_dump(mode="json")


class PineconeRecord(BaseModel):
    """Pinecone upsert용 레코드."""

    id: str = Field(description="product_{product_id}")
    values: list[float] = Field(description="512차원 CLIP 임베딩")
    metadata: dict = Field(default_factory=dict)

    def to_pinecone_dict(self) -> dict:
        """Pinecone upsert용 딕셔너리를 반환한다."""
        return {
            "id": self.id,
            "values": self.values,
            "metadata": self.metadata,
        }
