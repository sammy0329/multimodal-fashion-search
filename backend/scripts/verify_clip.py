"""CLIP ViT-B/32 모델 로드 및 임베딩 검증 스크립트.

사용법:
    python scripts/verify_clip.py

기대 결과:
    - 텍스트 임베딩: 512차원
    - 이미지 임베딩: 512차원
    - 텍스트-이미지 유사도 계산 성공
"""

import sys

import clip
import torch
from PIL import Image


def main() -> None:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"디바이스: {device}")

    print("CLIP ViT-B/32 모델 로드 중...")
    model, preprocess = clip.load("ViT-B/32", device=device)
    print("모델 로드 완료.")

    # 텍스트 임베딩
    text_inputs = clip.tokenize(["a white oversized shirt", "casual street style"])
    text_inputs = text_inputs.to(device)

    with torch.no_grad():
        text_features = model.encode_text(text_inputs)

    text_dim = text_features.shape[1]
    print(f"텍스트 임베딩 차원: {text_dim}")
    assert text_dim == 512, f"예상: 512, 실제: {text_dim}"

    # 이미지 임베딩 (더미 이미지)
    dummy_image = Image.new("RGB", (224, 224), color=(128, 128, 128))
    image_input = preprocess(dummy_image).unsqueeze(0).to(device)

    with torch.no_grad():
        image_features = model.encode_image(image_input)

    image_dim = image_features.shape[1]
    print(f"이미지 임베딩 차원: {image_dim}")
    assert image_dim == 512, f"예상: 512, 실제: {image_dim}"

    # 유사도 계산
    text_features = text_features / text_features.norm(dim=-1, keepdim=True)
    image_features = image_features / image_features.norm(dim=-1, keepdim=True)
    similarity = (image_features @ text_features.T).squeeze(0)

    print(f"텍스트-이미지 유사도: {similarity.cpu().numpy()}")
    print("\nCLIP 모델 검증 완료!")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"오류 발생: {e}", file=sys.stderr)
        sys.exit(1)
