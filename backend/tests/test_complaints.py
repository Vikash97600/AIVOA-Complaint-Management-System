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

    response = await async_client.get("/api/complaints?page=1&page_size=20")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 5
    assert data["page"] == 1


@pytest.mark.asyncio
async def test_qms_commit_lifecycle_and_snapshot(async_client: AsyncClient):
    """
    Test 8: Full QMS Commit Lifecycle & Frozen Snapshot Immutability.
    Verifies:
    1. Creating draft complaint and attaching preliminary AI risk assessment.
    2. Formally committing to QMS Ledger.
    3. Server-side QMS reference number generation (QMS-2026-XXXXXX).
    4. Retrieving frozen QMS ledger snapshot.
    5. Editing protection rejection on committed complaints.
    """
    # Step 1: Create draft complaint
    create_res = await async_client.post(
        "/api/complaints",
        json={
            "customer_name": "Apollo Pharmacy",
            "product_name": "Amoxicillin Capsules 500 mg",
            "batch_number": "BMX240602",
            "affected_quantity": "48 capsules",
            "complaint_category": "Product Defect",
            "complaint_description": "Discolored capsules observed inside sealed blister pack."
        }
    )
    assert create_res.status_code == 201
    complaint_id = create_res.json()["id"]

    # Attach risk assessment in DB
    from app.services.risk_assessment_service import save_or_update_risk_assessment
    from app.schemas.risk import RiskAssessmentCreate
    from app.dependencies import get_db

    # Get DB session override
    async for db in app.dependency_overrides[get_db]():
        await save_or_update_risk_assessment(
            db,
            complaint_id,
            RiskAssessmentCreate(
                severity_suggested="HIGH",
                complaint_category="Product Defect - Discoloration",
                suggested_next_action="Route to QA Investigation & Issue Replacement",
                risk_details="Visual defect affecting active batch lot.",
                requires_quarantine=True
            )
        )
        break

    # Step 2: Formally Commit to QMS Ledger via POST /api/complaints/{id}/commit
    commit_res = await async_client.post(f"/api/complaints/{complaint_id}/commit")
    assert commit_res.status_code == 200
    committed_data = commit_res.json()
    assert committed_data["status"] == "COMMITTED"
    assert committed_data["qms_reference_number"] is not None
    qms_ref = committed_data["qms_reference_number"]
    assert qms_ref.startswith("QMS-")

    # Step 3: Retrieve QMS Ledger Snapshot via GET /api/complaints/{id}/qms
    ledger_res = await async_client.get(f"/api/complaints/{complaint_id}/qms")
    assert ledger_res.status_code == 200
    ledger_data = ledger_res.json()
    assert ledger_data["qms_reference_number"] == qms_ref
    snapshot = ledger_data["frozen_payload_json"]
    assert snapshot["complaint"]["batch_number"] == "BMX240602"
    assert snapshot["complaint"]["affected_quantity"] == "48 capsules"
    assert snapshot["risk_assessment"]["severity_suggested"] == "HIGH"
    assert snapshot["risk_assessment"]["requires_quarantine"] is True

    # Step 4: Verify Committed Complaint Edit Protection (PATCH /api/complaints/{id})
    patch_res = await async_client.patch(
        f"/api/complaints/{complaint_id}",
        json={"batch_number": "ILLEGAL_MUTATION_123"}
    )
    assert patch_res.status_code == 409
    assert "already been committed" in patch_res.json()["detail"].lower()

    # Verify database data remained intact
    get_res = await async_client.get(f"/api/complaints/{complaint_id}")
    assert get_res.json()["batch_number"] == "BMX240602"


@pytest.mark.asyncio
async def test_commit_complaint_missing_risk_rejection(async_client: AsyncClient):
    """Test 9: Attempting to commit a complaint without a risk assessment is rejected."""
    create_res = await async_client.post(
        "/api/complaints",
        json={"customer_name": "Incomplete Client", "product_name": "Product X"}
    )
    complaint_id = create_res.json()["id"]

    commit_res = await async_client.post(f"/api/complaints/{complaint_id}/commit")
    assert commit_res.status_code == 400
    assert "risk assessment is unavailable" in commit_res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_commit_complaint_json_body_endpoint(async_client: AsyncClient):
    """Test 10: Formally committing via POST /api/complaints/commit JSON body endpoint."""
    create_res = await async_client.post(
        "/api/complaints",
        json={
            "customer_name": "Global Pharma Ltd",
            "product_name": "Paracetamol Tablets 500mg",
            "complaint_description": "Chipped tablets in foil blister."
        }
    )
    complaint_id = create_res.json()["id"]

    # Attach risk assessment
    from app.services.risk_assessment_service import save_or_update_risk_assessment
    from app.schemas.risk import RiskAssessmentCreate
    from app.dependencies import get_db

    async for db in app.dependency_overrides[get_db]():
        await save_or_update_risk_assessment(
            db,
            complaint_id,
            RiskAssessmentCreate(
                severity_suggested="LOW",
                complaint_category="Packaging Defect",
                suggested_next_action="Inspect retained sample",
                risk_details="Minor chipping",
                requires_quarantine=False
            )
        )
        break

    # Body endpoint commit
    commit_res = await async_client.post("/api/complaints/commit", json={"complaint_id": complaint_id})
    assert commit_res.status_code == 200
    data = commit_res.json()
    assert data["status"] == "COMMITTED"
    assert data["qms_reference_number"].startswith("QMS-")


@pytest.mark.asyncio
async def test_list_complaints_filtering_and_search(async_client: AsyncClient):
    """Test 11 (Prompt 17.1): Complaint history filtering by status and search keyword."""
    # Create DRAFT complaint
    res1 = await async_client.post(
        "/api/complaints",
        json={
            "customer_name": "Apollo Pharmacy",
            "product_name": "Amoxicillin Capsules 500 mg",
            "batch_number": "AMX240602",
        }
    )
    assert res1.status_code == 201

    # Create second DRAFT complaint
    res2 = await async_client.post(
        "/api/complaints",
        json={
            "customer_name": "Fortis Healthcare",
            "product_name": "Ciprofloxacin IV 200mg",
            "batch_number": "CIP990101",
        }
    )
    assert res2.status_code == 201
    cid2 = res2.json()["id"]

    # Attach risk and commit the second complaint
    from app.services.risk_assessment_service import save_or_update_risk_assessment
    from app.schemas.risk import RiskAssessmentCreate
    from app.dependencies import get_db

    async for db in app.dependency_overrides[get_db]():
        await save_or_update_risk_assessment(
            db,
            cid2,
            RiskAssessmentCreate(
                severity_suggested="MEDIUM",
                complaint_category="Packaging Defect",
                suggested_next_action="Review batch record",
                risk_details="Minor defect",
                requires_quarantine=False
            )
        )
        break

    await async_client.post(f"/api/complaints/{cid2}/commit")

    # Filter status=DRAFT
    draft_res = await async_client.get("/api/complaints?status=DRAFT")
    assert draft_res.status_code == 200
    draft_items = draft_res.json()["items"]
    assert all(item["status"] == "DRAFT" for item in draft_items)
    assert any(item["customer_name"] == "Apollo Pharmacy" for item in draft_items)

    # Filter status=COMMITTED
    committed_res = await async_client.get("/api/complaints?status=COMMITTED")
    assert committed_res.status_code == 200
    committed_items = committed_res.json()["items"]
    assert all(item["status"] == "COMMITTED" for item in committed_items)
    assert any(item["customer_name"] == "Fortis Healthcare" for item in committed_items)

    # Search keyword
    search_res = await async_client.get("/api/complaints?search=Apollo")
    assert search_res.status_code == 200
    search_items = search_res.json()["items"]
    assert len(search_items) == 1
    assert search_items[0]["customer_name"] == "Apollo Pharmacy"


@pytest.mark.asyncio
async def test_get_complaint_full_detail_payload(async_client: AsyncClient):
    """Test 12 (Prompt 17.1): GET /api/complaints/{id} returns complete detail with risk assessment."""
    create_res = await async_client.post(
        "/api/complaints",
        json={
            "customer_name": "Apollo Pharmacy",
            "product_name": "Amoxicillin Capsules",
            "strength_grade": "500 mg",
            "batch_number": "AMX240602",
            "affected_quantity": "12 capsules"
        }
    )
    complaint_id = create_res.json()["id"]

    # Attach risk
    from app.services.risk_assessment_service import save_or_update_risk_assessment
    from app.schemas.risk import RiskAssessmentCreate
    from app.dependencies import get_db

    async for db in app.dependency_overrides[get_db]():
        await save_or_update_risk_assessment(
            db,
            complaint_id,
            RiskAssessmentCreate(
                severity_suggested="HIGH",
                complaint_category="Product Defect",
                suggested_next_action="Quarantine batch",
                risk_details="Discoloration risk",
                requires_quarantine=True
            )
        )
        break

    detail_res = await async_client.get(f"/api/complaints/{complaint_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["id"] == complaint_id
    assert detail["customer_name"] == "Apollo Pharmacy"
    assert detail["product_name"] == "Amoxicillin Capsules"
    assert detail["risk_assessment"] is not None
    assert detail["risk_assessment"]["severity_suggested"] == "HIGH"
    assert detail["risk_assessment"]["requires_quarantine"] is True


