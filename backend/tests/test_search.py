from httpx import AsyncClient


async def test_search_returns_501(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/search",
        json={"query": "오버핏 셔츠"},
    )

    assert response.status_code == 501
    assert "구현 예정" in response.json()["detail"]


async def test_search_validates_limit(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/search",
        json={"query": "셔츠", "limit": 0},
    )

    assert response.status_code == 422
