import io

from PIL import Image

CLIP_IMAGE_SIZE = 224
MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10MB
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP", "BMP", "GIF"}


def validate_image(image_bytes: bytes) -> None:
    """이미지 바이트의 유효성을 검증한다.

    Args:
        image_bytes: 원본 이미지 바이트.

    Raises:
        ValueError: 유효하지 않은 이미지일 때.
    """
    if len(image_bytes) == 0:
        raise ValueError("이미지 데이터가 비어 있습니다")

    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise ValueError(
            f"이미지 크기가 {MAX_IMAGE_BYTES // (1024 * 1024)}MB를 초과합니다"
        )

    try:
        image = Image.open(io.BytesIO(image_bytes))
        image.verify()
    except Exception as exc:
        raise ValueError("유효하지 않은 이미지 형식입니다") from exc

    image = Image.open(io.BytesIO(image_bytes))
    if image.format and image.format not in ALLOWED_FORMATS:
        raise ValueError(
            f"지원하지 않는 이미지 형식입니다: {image.format}. "
            f"지원 형식: {', '.join(sorted(ALLOWED_FORMATS))}"
        )


def preprocess_image(image_bytes: bytes) -> Image.Image:
    """이미지 바이트를 CLIP 입력용 224x224 RGB 이미지로 변환한다.

    Args:
        image_bytes: 원본 이미지 바이트.

    Returns:
        224x224 RGB PIL Image.

    Raises:
        ValueError: 유효하지 않은 이미지일 때.
    """
    validate_image(image_bytes)

    image = Image.open(io.BytesIO(image_bytes))
    image = image.convert("RGB")
    image = image.resize(
        (CLIP_IMAGE_SIZE, CLIP_IMAGE_SIZE),
        Image.Resampling.LANCZOS,
    )
    return image
