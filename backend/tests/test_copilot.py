import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.main import app
from app.database.models import Base
from app.dependencies import get_db

@pytest.fixture
async def async_client():
    # Use SQLite in-memory engine for API testing
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
    await test_engine.dispose()


@pytest.mark.asyncio
async def test_copilot_log_complaint_endpoint(async_client: AsyncClient):
    """Test POST /api/copilot/message with Log Complaint prompt."""
    payload = {
        "message": "Apollo Pharmacy reported discolored capsules in Amoxicillin Capsules 500 mg."
    }
    response = await async_client.post("/api/copilot/message", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "LOG_COMPLAINT"
    assert "Log Complaint workflow selected" in data["message"]


@pytest.mark.asyncio
async def test_copilot_edit_complaint_endpoint(async_client: AsyncClient):
    """Test POST /api/copilot/message with Edit Complaint prompt."""
    payload = {
        "message": "Sorry, the batch number is BMX240602 and affected quantity is 48 capsules."
    }
    response = await async_client.post("/api/copilot/message", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "EDIT_COMPLAINT"
    assert "Edit Complaint workflow selected" in data["message"]


@pytest.mark.asyncio
async def test_copilot_document_extraction_endpoint(async_client: AsyncClient):
    """Test POST /api/copilot/message with Document Extraction prompt."""
    payload = {
        "message": "Please extract the complaint information from this PDF."
    }
    response = await async_client.post("/api/copilot/message", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "DOCUMENT_EXTRACTION"
    assert "Document Extraction workflow selected" in data["message"]


@pytest.mark.asyncio
async def test_copilot_unknown_endpoint(async_client: AsyncClient):
    """Test POST /api/copilot/message with Unknown / General prompt."""
    payload = {
        "message": "Hello AIVOA"
    }
    response = await async_client.post("/api/copilot/message", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "UNKNOWN"
    assert "AIVOA Copilot is ready" in data["message"]


@pytest.mark.asyncio
async def test_copilot_with_active_complaint_id(async_client: AsyncClient):
    """Test POST /api/copilot/message with active complaint_id context."""
    # Create draft complaint
    create_res = await async_client.post("/api/complaints", json={"customer_name": "Apollo Pharmacy"})
    complaint_id = create_res.json()["id"]

    payload = {
        "message": "Sorry, batch number is BMX240602.",
        "complaint_id": complaint_id
    }
    response = await async_client.post("/api/copilot/message", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "EDIT_COMPLAINT"
    assert data["complaint"] is not None
    assert data["complaint"]["id"] == complaint_id
    assert data["complaint"]["customer_name"] == "Apollo Pharmacy"
