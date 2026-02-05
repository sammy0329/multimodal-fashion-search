from httpx import AsyncClient


async def test_recommend_returns_501(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/recommend",
        json={"product_ids": ["product_001"]},
    )

    assert response.status_code == 501
    assert "구현 예정" in response.json()["detail"]


async def test_recommend_validates_empty_product_ids(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/recommend",
        json={"product_ids": []},
    )

    assert response.status_code == 422
