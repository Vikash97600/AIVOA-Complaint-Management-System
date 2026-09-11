import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.main import app
from app.database.models import Base
from app.dependencies import get_db
from app.services.completeness_service import calculate_completeness
from app.services.duplicate_detection_service import detect_duplicate_complaints
from app.services.summary_service import generate_complaint_summary

@pytest.fixture
async def async_client():
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
async def test_completeness_checker_full_data():
    """Test 1: Completeness checker with complete complaint data."""
    complaint_data = {
        "customer_name": "Apollo Pharmacy",
        "product_name": "Amoxicillin Capsules 500 mg",
        "batch_number": "AMX240602",
        "affected_quantity": "12 capsules",
        "complaint_description": "Discolored capsules observed inside blister pack.",
        "expiry_date": "February 2028",
        "manufacturing_date": "March 2026",
        "strength_grade": "500 mg"
    }
    res = calculate_completeness(complaint_data)
    assert res.is_complete is True
    assert res.completion_score == 100
    assert res.status_label == "Complete"
    assert len(res.missing_fields) == 0


@pytest.mark.asyncio
async def test_completeness_checker_missing_fields():
    """Test 2: Completeness checker identifies missing batch and expiry date."""
    complaint_data = {
        "customer_name": "Metro Pharma",
        "product_name": "Paracetamol Tablets 500 mg",
        "complaint_description": "Chipped tablets in blister pack."
    }
    res = calculate_completeness(complaint_data)
    assert res.is_complete is False
    assert "batch_number" in res.missing_fields
    assert "affected_quantity" in res.missing_fields
    assert len(res.warnings) > 0
    assert len(res.recommendations) > 0


@pytest.mark.asyncio
async def test_duplicate_detection_matching_candidate(async_client: AsyncClient):
    """Test 3: Duplicate detection identifies existing matching complaint by Product & Batch."""
    # 1. Create existing complaint
    create_res = await async_client.post(
        "/api/complaints",
        json={
            "customer_name": "Apollo Pharmacy",
            "product_name": "Amoxicillin Capsules 500 mg",
            "batch_number": "AMX240602",
            "affected_quantity": "12 capsules",
            "complaint_category": "Product Defect"
        }
    )
    existing_id = create_res.json()["id"]

    # 2. Query duplicate detection for similar new complaint payload
    async for db in app.dependency_overrides[get_db]():
        dup_res = await detect_duplicate_complaints(
            db,
            {
                "customer_name": "Apollo Pharmacy",
                "product_name": "Amoxicillin Capsules 500 mg",
                "batch_number": "AMX240602",
                "affected_quantity": "48 capsules",
            }
        )
        assert dup_res.is_duplicate is True
        assert dup_res.confidence >= 0.70
        assert dup_res.matched_complaint_id == existing_id
        assert len(dup_res.matches) > 0
        break


@pytest.mark.asyncio
async def test_complaint_summary_generator():
    """Test 4: Complaint summary service generates factual executive overview."""
    complaint_data = {
        "customer_name": "Apollo Pharmacy",
        "product_name": "Amoxicillin Capsules 500 mg",
        "batch_number": "AMX240602",
        "affected_quantity": "12 capsules",
        "complaint_description": "Discolored capsules observed."
    }
    risk_data = {
        "severity_suggested": "HIGH",
        "complaint_category": "Product Defect - Discoloration"
    }

    res = await generate_complaint_summary(complaint_data, risk_data)
    assert res.summary_text is not None
    assert len(res.summary_text) > 20
    assert len(res.key_facts) >= 3


@pytest.mark.asyncio
async def test_bonus_rest_api_endpoints(async_client: AsyncClient):
    """Test 5: REST Endpoints for Completeness, Duplicates, and Summary."""
    create_res = await async_client.post(
        "/api/complaints",
        json={
            "customer_name": "ABC Formulations Ltd",
            "product_name": "Metformin Hydrochloride API",
            "strength_grade": "IP/BP",
            "batch_number": "MFM202606",
            "affected_quantity": "25 kg",
            "complaint_description": "Foreign particles observed in HDPE drum."
        }
    )
    complaint_id = create_res.json()["id"]

    # 1. POST /api/complaints/{id}/completeness
    comp_res = await async_client.post(f"/api/complaints/{complaint_id}/completeness")
    assert comp_res.status_code == 200
    assert "completion_score" in comp_res.json()

    # 2. POST /api/complaints/{id}/duplicates
    dup_res = await async_client.post(f"/api/complaints/{complaint_id}/duplicates")
    assert dup_res.status_code == 200
    assert "is_duplicate" in dup_res.json()

    # 3. POST /api/complaints/{id}/summary
    sum_res = await async_client.post(f"/api/complaints/{complaint_id}/summary")
    assert sum_res.status_code == 200
    assert "summary_text" in sum_res.json()
