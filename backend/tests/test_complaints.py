import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.main import app
from app.database.models import Base
from app.dependencies import get_db

@pytest.fixture
async def async_client():
    # Use SQLite in-memory engine for API integration testing
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
async def test_health_endpoints(async_client: AsyncClient):
    """Test 1 & 2: GET /api/health and GET /api/health/database."""
    response = await async_client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "AIVOA" in data["service"]

    db_response = await async_client.get("/api/health/database")
    assert db_response.status_code == 200
    assert db_response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_create_complaint_api(async_client: AsyncClient):
    """Test 3: POST /api/complaints creates a draft complaint."""
    payload = {
        "customer_name": "Apollo Pharmacy",
        "product_name": "Amoxicillin Capsules 500 mg",
        "batch_number": "AMX240602",
        "affected_quantity": "12 capsules",
        "manufacturing_date": "March 2026",
        "expiry_date": "February 2028"
    }
    response = await async_client.post("/api/complaints", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["status"] == "DRAFT"
    assert data["customer_name"] == "Apollo Pharmacy"
    assert data["product_name"] == "Amoxicillin Capsules 500 mg"
    assert data["batch_number"] == "AMX240602"
    assert data["affected_quantity"] == "12 capsules"


@pytest.mark.asyncio
async def test_get_complaint_api(async_client: AsyncClient):
    """Test 4: GET /api/complaints/{id} retrieves created complaint."""
    payload = {
        "customer_name": "ABC Formulations Ltd.",
        "product_name": "Metformin Hydrochloride API",
        "strength_grade": "IP/BP",
        "affected_quantity": "25 kg"
    }
    create_res = await async_client.post("/api/complaints", json=payload)
    complaint_id = create_res.json()["id"]

    get_res = await async_client.get(f"/api/complaints/{complaint_id}")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["id"] == complaint_id
    assert data["customer_name"] == "ABC Formulations Ltd."
    assert data["product_name"] == "Metformin Hydrochloride API"
    assert data["strength_grade"] == "IP/BP"


@pytest.mark.asyncio
async def test_partial_update_complaint_api(async_client: AsyncClient):
    """
    Test 5: PATCH /api/complaints/{id} updates ONLY specified fields.
    Verifies that non-supplied fields remain completely intact (Safe Delta Merge).
    """
    initial_payload = {
        "customer_name": "Apollo Pharmacy",
        "product_name": "Amoxicillin Capsules",
        "strength_grade": "500 mg",
        "batch_number": "AMX240602",
        "affected_quantity": "12 capsules",
        "manufacturing_date": "March 2026",
        "expiry_date": "February 2028"
    }
    create_res = await async_client.post("/api/complaints", json=initial_payload)
    complaint_id = create_res.json()["id"]

    # Partial edit request (changing batch and quantity only)
    patch_payload = {
        "batch_number": "BMX240602",
        "affected_quantity": "48 capsules"
    }
    patch_res = await async_client.patch(f"/api/complaints/{complaint_id}", json=patch_payload)
    assert patch_res.status_code == 200
    data = patch_res.json()

    # Modified fields
    assert data["batch_number"] == "BMX240602"
    assert data["affected_quantity"] == "48 capsules"

    # Preserved fields
    assert data["customer_name"] == "Apollo Pharmacy"
    assert data["product_name"] == "Amoxicillin Capsules"
    assert data["strength_grade"] == "500 mg"
    assert data["manufacturing_date"] == "March 2026"
    assert data["expiry_date"] == "February 2028"


@pytest.mark.asyncio
async def test_complaint_not_found(async_client: AsyncClient):
    """Test 6: Requesting a non-existent UUID returns 404."""
    random_uuid = str(uuid.uuid4())
    response = await async_client.get(f"/api/complaints/{random_uuid}")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_list_complaints_pagination(async_client: AsyncClient):
    """Test 7: GET /api/complaints with pagination."""
    for i in range(5):
        await async_client.post("/api/complaints", json={"customer_name": f"Facility {i}"})

    response = await async_client.get("/api/complaints?page=1&page_size=2")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert len(data["items"]) == 2
