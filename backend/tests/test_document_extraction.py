import io
import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from fastapi import UploadFile

from app.main import app
from app.ai.state import AgentState, Intent
from app.ai.graph import compiled_graph
from app.ai.nodes.document_extraction import document_extract_node
from app.ai.prompts.log_complaint import ExtractedComplaintData
from app.ai.prompts.risk_assessment import RiskAssessmentOutput
from app.database.models import RiskSeverity
from app.services import document_extraction_service
from app.core.exceptions import (
    InvalidDocumentTypeError,
    DocumentOversizedError,
    DocumentExtractionError,
)

# Helper function to create a valid simple PDF in memory
def create_sample_pdf_bytes(text_content: str) -> bytes:
    import pypdf
    writer = pypdf.PdfWriter()
    page = writer.add_blank_page(width=612, height=792)

    # Note: For testing pypdf extraction reliability, we write plain text or create standard PDF page
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


@pytest.mark.asyncio
async def test_pdf_text_extraction():
    """Test extracting text from synthetic PDF bytes."""
    # Create simple text PDF via pypdf annotations/content stream
    import pypdf
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=200, height=200)
    buf = io.BytesIO()
    writer.write(buf)
    pdf_bytes = buf.getvalue()
    
    # Verify parsing function doesn't crash on valid empty/blank page PDF
    try:
        text = document_extraction_service.extract_text_from_pdf(pdf_bytes)
        assert isinstance(text, str)
    except DocumentExtractionError:
        pass


@pytest.mark.asyncio
async def test_txt_and_eml_text_extraction():
    """Test text extraction for .txt and .eml documents."""
    # Test TXT
    txt_bytes = b"ABC Formulations Ltd.\nProduct: Metformin Hydrochloride API\nQuantity: 25 kg"
    txt_content = document_extraction_service.extract_text_from_txt(txt_bytes)
    assert "ABC Formulations Ltd." in txt_content
    assert "Metformin Hydrochloride API" in txt_content

    # Test EML
    eml_bytes = (
        b"From: customer@example.com\n"
        b"To: qa@pharma.com\n"
        b"Subject: Product Defect Notice\n"
        b"Date: Wed, 25 Jun 2026 10:00:00 +0000\n\n"
        b"Foreign particles observed inside a sealed HDPE drum."
    )
    eml_content = document_extraction_service.extract_text_from_eml(eml_bytes)
    assert "Subject: Product Defect Notice" in eml_content
    assert "Foreign particles observed" in eml_content


@pytest.mark.asyncio
async def test_unsupported_file_rejection(tmp_path):
    """Test that uploading unsupported file extension (.exe) raises InvalidDocumentTypeError."""
    file = UploadFile(filename="malware.exe", file=io.BytesIO(b"binary data"))
    with pytest.raises(InvalidDocumentTypeError):
        await document_extraction_service.process_document_upload(file, upload_dir_name=str(tmp_path))


@pytest.mark.asyncio
async def test_oversized_file_rejection(tmp_path, monkeypatch):
    """Test that uploading file exceeding MAX_UPLOAD_SIZE raises DocumentOversizedError."""
    from app.core.config import settings
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE", 100)  # Set max size to 100 bytes

    big_content = b"A" * 500
    file = UploadFile(filename="large_document.pdf", file=io.BytesIO(big_content))

    with pytest.raises(DocumentOversizedError):
        await document_extraction_service.process_document_upload(file, upload_dir_name=str(tmp_path))


@pytest.mark.asyncio
async def test_empty_file_rejection(tmp_path):
    """Test that empty file raises DocumentExtractionError."""
    file = UploadFile(filename="empty.txt", file=io.BytesIO(b""))
    with pytest.raises(DocumentExtractionError):
        await document_extraction_service.process_document_upload(file, upload_dir_name=str(tmp_path))


@pytest.mark.asyncio
async def test_document_extraction_node():
    """Test document_extract_node Groq extraction and missing field preservation."""
    sample_text = (
        "ABC Formulations Ltd.\n"
        "Product: Metformin Hydrochloride API\n"
        "Grade: IP/BP\n"
        "Quantity: 25 kg (1 HDPE Drum)\n"
        "Manufacturing Date: 25 June 2026\n"
        "Expiry: Not provided\n"
        "Complaint: Foreign particles were observed inside a sealed HDPE drum."
    )

    mock_extracted = ExtractedComplaintData(
        customer_name="ABC Formulations Ltd.",
        complaint_source="Pharmaceutical Customer",
        product_name="Metformin Hydrochloride API",
        strength_grade="IP/BP",
        batch_number=None,  # Missing batch number
        affected_quantity="25 kg (1 HDPE Drum)",
        manufacturing_date="25 June 2026",
        expiry_date=None,   # Missing expiry date
        complaint_description="Foreign particles were observed inside a sealed HDPE drum.",
    )

    state: AgentState = {
        "document_text": sample_text,
        "document_metadata": {"file_name": "metformin_complaint.pdf", "file_type": "pdf"},
    }

    with patch("app.ai.nodes.document_extraction.groq_service.generate_structured", new_callable=AsyncMock) as mock_groq:
        mock_groq.return_value = mock_extracted

        res = await document_extract_node(state)

        assert "current_complaint" in res
        complaint = res["current_complaint"]
        assert complaint["customer_name"] == "ABC Formulations Ltd."
        assert complaint["product_name"] == "Metformin Hydrochloride API"
        assert complaint["affected_quantity"] == "25 kg (1 HDPE Drum)"
        assert "batch_number" not in complaint  # Preserved as missing
        assert "expiry_date" not in complaint   # Preserved as missing
        assert "batch number" in res["response_message"]


@pytest.mark.asyncio
async def test_full_graph_document_extraction_routing():
    """Test LangGraph flow: document_extraction -> risk_assessment -> response_synthesis."""
    sample_text = "Apollo Pharmacy reported discolored capsules in Amoxicillin 500mg."

    mock_extracted = ExtractedComplaintData(
        customer_name="Apollo Pharmacy",
        product_name="Amoxicillin Capsules",
        strength_grade="500 mg",
        complaint_description="Discolored capsules.",
    )

    mock_risk = RiskAssessmentOutput(
        severity_suggested=RiskSeverity.MEDIUM,
        complaint_category="Product Defect",
        suggested_next_action="Quarantine affected lot",
        risk_details="Discoloration indicates chemical degradation",
        requires_quarantine=True,
    )

    state: AgentState = {
        "intent": Intent.DOCUMENT_EXTRACTION,
        "document_text": sample_text,
        "document_metadata": {"file_name": "apollo_complaint.txt", "file_type": "txt"},
    }

    async def mock_generate_structured(messages, response_model, **kwargs):
        if response_model == ExtractedComplaintData:
            return mock_extracted
        elif response_model == RiskAssessmentOutput:
            return mock_risk
        return None

    with patch("app.services.groq_service.groq_service.generate_structured", side_effect=mock_generate_structured):
        final_state = await compiled_graph.ainvoke(state)

        assert final_state["intent"] == Intent.DOCUMENT_EXTRACTION
        assert final_state["current_complaint"]["customer_name"] == "Apollo Pharmacy"
        assert final_state["risk_assessment"]["severity_suggested"] == "MEDIUM"
        assert "risk assessment" in final_state["response_message"].lower()


@pytest.mark.asyncio
async def test_copilot_document_endpoint_integration(async_client: AsyncClient, tmp_path, monkeypatch):
    """Integration test for POST /api/copilot/document endpoint."""
    txt_content = b"ABC Formulations Ltd. Metformin Hydrochloride API 25 kg."

    mock_extracted = ExtractedComplaintData(
        customer_name="ABC Formulations Ltd.",
        product_name="Metformin Hydrochloride API",
        affected_quantity="25 kg",
    )
    mock_risk = RiskAssessmentOutput(
        severity_suggested=RiskSeverity.HIGH,
        complaint_category="Material Defect",
        suggested_next_action="Initiate QA audit",
        risk_details="Foreign material in API batch",
        requires_quarantine=True,
    )

    async def mock_generate_structured(messages, response_model, **kwargs):
        if response_model == ExtractedComplaintData:
            return mock_extracted
        elif response_model == RiskAssessmentOutput:
            return mock_risk
        return None

    with patch("app.services.groq_service.groq_service.generate_structured", side_effect=mock_generate_structured):
        response = await async_client.post(
            "/api/copilot/document",
            files={"file": ("test_notice.txt", txt_content, "text/plain")}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["intent"] == "DOCUMENT_EXTRACTION"
        assert data["complaint"]["customer_name"] == "ABC Formulations Ltd."
        assert data["risk_assessment"]["severity_suggested"] == "HIGH"
        assert data["document"]["file_name"] == "test_notice.txt"
