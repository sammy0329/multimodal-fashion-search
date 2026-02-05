import io

import pytest
from PIL import Image

from app.utils.image import (
    CLIP_IMAGE_SIZE,
    MAX_IMAGE_BYTES,
    preprocess_image,
    validate_image,
)


def _create_test_image(width: int = 640, height: int = 480, fmt: str = "PNG") -> bytes:
    image = Image.new("RGB", (width, height), color=(255, 0, 0))
    buffer = io.BytesIO()
    image.save(buffer, format=fmt)
    return buffer.getvalue()


class TestValidateImage:
    def test_valid_png(self) -> None:
        image_bytes = _create_test_image(fmt="PNG")
        validate_image(image_bytes)

    def test_valid_jpeg(self) -> None:
        image_bytes = _create_test_image(fmt="JPEG")
        validate_image(image_bytes)

    def test_empty_bytes_raises(self) -> None:
        with pytest.raises(ValueError, match="비어 있습니다"):
            validate_image(b"")

    def test_oversized_image_raises(self) -> None:
        oversized = b"\x00" * (MAX_IMAGE_BYTES + 1)
        with pytest.raises(ValueError, match="초과합니다"):
            validate_image(oversized)

    def test_invalid_format_raises(self) -> None:
        with pytest.raises(ValueError, match="유효하지 않은"):
            validate_image(b"not an image")


class TestPreprocessImage:
    def test_output_size(self) -> None:
        image_bytes = _create_test_image(width=800, height=600)
        result = preprocess_image(image_bytes)

        assert result.size == (CLIP_IMAGE_SIZE, CLIP_IMAGE_SIZE)

    def test_output_mode_rgb(self) -> None:
        image_bytes = _create_test_image()
        result = preprocess_image(image_bytes)

        assert result.mode == "RGB"

    def test_rgba_converted_to_rgb(self) -> None:
        image = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        image_bytes = buffer.getvalue()

        result = preprocess_image(image_bytes)

        assert result.mode == "RGB"
        assert result.size == (CLIP_IMAGE_SIZE, CLIP_IMAGE_SIZE)

    def test_invalid_bytes_raises(self) -> None:
        with pytest.raises(ValueError):
            preprocess_image(b"invalid data")
