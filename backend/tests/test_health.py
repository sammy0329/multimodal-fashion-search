from httpx import AsyncClient


async def test_health_returns_ok(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


async def test_health_includes_version(client: AsyncClient) -> None:
    response = await client.get("/health")

    data = response.json()
    assert data["version"] == "0.1.0"
