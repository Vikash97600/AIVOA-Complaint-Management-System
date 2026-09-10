import pytest
import pytest_asyncio
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.exc import IntegrityError
from app.database.models import (
    Base,
    Complaint,
    RiskAssessment,
    ComplaintDocument,
    QMSLedger,
    ComplaintStatus,
    RiskSeverity,
)

@pytest_asyncio.fixture
async def async_session():
    # Use SQLite in-memory engine for database unit tests
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await test_engine.dispose()


@pytest.mark.asyncio
async def test_create_partial_complaint(async_session: AsyncSession):
    """Test 1: Complaint can be created with partial information; optional fields remain NULL."""
    complaint = Complaint(
        customer_name="Apollo Pharmacy",
        product_name="Amoxicillin Capsules 500 mg",
        batch_number="AMX240602"
    )
    async_session.add(complaint)
    await async_session.commit()
    await async_session.refresh(complaint)

    assert complaint.id is not None
    assert complaint.status == ComplaintStatus.DRAFT
    assert complaint.customer_name == "Apollo Pharmacy"
    assert complaint.product_name == "Amoxicillin Capsules 500 mg"
    assert complaint.batch_number == "AMX240602"
    assert complaint.qms_reference_number is None
    assert complaint.affected_quantity is None


@pytest.mark.asyncio
async def test_risk_assessment_relationship(async_session: AsyncSession):
    """Test 2: RiskAssessment 1-to-1 relationship with Complaint."""
    complaint = Complaint(
        customer_name="Apollo Pharmacy",
        product_name="Amoxicillin Capsules",
        defect_type="Discoloration"
    )
    async_session.add(complaint)
    await async_session.flush()

    risk = RiskAssessment(
        complaint_id=complaint.id,
        severity_suggested=RiskSeverity.HIGH,
        complaint_category="Quality Defect",
        suggested_next_action="Quarantine batch AMX240602 and initiate lab analysis",
        risk_details="Discoloration suggests chemical degradation.",
        requires_quarantine=True
    )
    async_session.add(risk)
    await async_session.commit()
    await async_session.refresh(complaint)

    assert complaint.risk_assessment is not None
    assert complaint.risk_assessment.severity_suggested == RiskSeverity.HIGH
    assert complaint.risk_assessment.requires_quarantine is True


@pytest.mark.asyncio
async def test_document_relationship(async_session: AsyncSession):
    """Test 3: Complaint 1-to-many relationship with ComplaintDocument."""
    complaint = Complaint(
        customer_name="ABC Formulations Ltd.",
        product_name="Metformin Hydrochloride API"
    )
    async_session.add(complaint)
    await async_session.flush()

    doc1 = ComplaintDocument(
        complaint_id=complaint.id,
        file_name="complaint_form.pdf",
        file_path="uploads/complaint_form_uuid1.pdf",
        file_type="application/pdf",
        extracted_text="Dark foreign particles observed in HDPE drum."
    )
    doc2 = ComplaintDocument(
        complaint_id=complaint.id,
        file_name="customer_email.pdf",
        file_path="uploads/customer_email_uuid2.pdf",
        file_type="application/pdf",
        extracted_text="Email report regarding Metformin API batch."
    )
    async_session.add_all([doc1, doc2])
    await async_session.commit()
    await async_session.refresh(complaint)

    assert len(complaint.documents) == 2
    filenames = [d.file_name for d in complaint.documents]
    assert "complaint_form.pdf" in filenames
    assert "customer_email.pdf" in filenames


@pytest.mark.asyncio
async def test_qms_ledger_snapshot(async_session: AsyncSession):
    """Test 4: QMSLedger snapshot storage with frozen JSON payload."""
    complaint = Complaint(
        status=ComplaintStatus.COMMITTED,
        qms_reference_number="QMS-2026-0001",
        customer_name="Apollo Pharmacy",
        product_name="Amoxicillin Capsules 500 mg",
        batch_number="AMX240602"
    )
    async_session.add(complaint)
    await async_session.flush()

    payload = {
        "customer_name": "Apollo Pharmacy",
        "product_name": "Amoxicillin Capsules 500 mg",
        "batch_number": "AMX240602",
        "affected_quantity": "12 capsules",
        "committed_status": "COMMITTED"
    }

    ledger_entry = QMSLedger(
        complaint_id=complaint.id,
        qms_reference_number="QMS-2026-0001",
        frozen_payload_json=payload
    )
    async_session.add(ledger_entry)
    await async_session.commit()
    await async_session.refresh(complaint)

    assert complaint.qms_ledger is not None
    assert complaint.qms_ledger.qms_reference_number == "QMS-2026-0001"
    assert complaint.qms_ledger.frozen_payload_json["batch_number"] == "AMX240602"


@pytest.mark.asyncio
async def test_unique_qms_reference_constraint(async_session: AsyncSession):
    """Test 5: Unique QMS reference number constraint enforcement."""
    c1 = Complaint(status=ComplaintStatus.COMMITTED, qms_reference_number="QMS-2026-0001")
    c2 = Complaint(status=ComplaintStatus.COMMITTED, qms_reference_number="QMS-2026-0001")
    
    async_session.add(c1)
    await async_session.commit()

    async_session.add(c2)
    with pytest.raises(IntegrityError):
        await async_session.commit()


@pytest.mark.asyncio
async def test_complaint_status_lifecycle(async_session: AsyncSession):
    """Test 6: Complaint status transitions from DRAFT to COMMITTED."""
    complaint = Complaint(customer_name="Apollo Pharmacy")
    async_session.add(complaint)
    await async_session.commit()

    assert complaint.status == ComplaintStatus.DRAFT

    complaint.status = ComplaintStatus.COMMITTED
    complaint.qms_reference_number = "QMS-2026-0002"
    await async_session.commit()
    await async_session.refresh(complaint)

    assert complaint.status == ComplaintStatus.COMMITTED
    assert complaint.qms_reference_number == "QMS-2026-0002"
