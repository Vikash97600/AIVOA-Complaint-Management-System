import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_health_check():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "AIVOA" in data["service"]

@pytest.mark.asyncio
async def test_ai_health_check():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health/ai")
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "groq"
        assert data["model"] == "gemma2-9b-it"
        assert "configured" in data
