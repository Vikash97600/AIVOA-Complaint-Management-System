import pytest
from unittest.mock import AsyncMock, patch
from app.ai.nodes.risk_assessment import risk_assessment_node
from app.ai.prompts.risk_assessment import RiskAssessmentOutput
from app.ai.state import AgentState, Intent
from app.database.models import RiskSeverity
from app.core.ai_exceptions import LLMServiceError
from app.ai.graph import compiled_graph


@pytest.mark.asyncio
async def test_apollo_pharmacy_risk_assessment():
    """Test 1: Verify AI risk assessment for Apollo Pharmacy complaint example."""
    mock_risk = RiskAssessmentOutput(
        severity_suggested=RiskSeverity.HIGH,
        complaint_category="Product Defect",
        suggested_next_action="Route to QA Investigation and verify retain samples",
        risk_details="Discoloration in capsules indicates a potential physical or formulation defect requiring investigation of the affected batch.",
        requires_quarantine=True,
    )

    state: AgentState = {
        "current_complaint": {
            "customer_name": "Apollo Pharmacy",
            "product_name": "Amoxicillin Capsules",
            "strength_grade": "500 mg",
            "batch_number": "AMX240602",
            "affected_quantity": "12 capsules",
            "defect_type": "Discoloration",
            "complaint_category": "Product Defect",
            "complaint_description": "Apollo Pharmacy reported 12 discolored capsules.",
        }
    }

    with patch(
        "app.ai.nodes.risk_assessment.groq_service.generate_structured",
        new_callable=AsyncMock,
        return_value=mock_risk,
    ):
        res = await risk_assessment_node(state)
        risk = res["risk_assessment"]

        assert risk["severity_suggested"] == "HIGH"
        assert risk["complaint_category"] == "Product Defect"
        assert risk["requires_quarantine"] is True
        assert "QA Investigation" in risk["suggested_next_action"]


@pytest.mark.asyncio
async def test_critical_contamination_risk_assessment():
    """Test 2: Verify CRITICAL severity risk assessment for foreign particle contamination."""
    mock_risk = RiskAssessmentOutput(
        severity_suggested=RiskSeverity.CRITICAL,
        complaint_category="Contamination",
        suggested_next_action="Quarantine affected material immediately and escalate to QA Lead",
        risk_details="Foreign particulate matter inside sealed product container indicates a severe quality hazard.",
        requires_quarantine=True,
    )

    state: AgentState = {
        "current_complaint": {
            "product_name": "Injectable Solution",
            "batch_number": "INJ99001",
            "defect_type": "Foreign Particulate Matter",
            "complaint_description": "Customer reported foreign particles inside a sealed product container.",
        }
    }

    with patch(
        "app.ai.nodes.risk_assessment.groq_service.generate_structured",
        new_callable=AsyncMock,
        return_value=mock_risk,
    ):
        res = await risk_assessment_node(state)
        risk = res["risk_assessment"]

        assert risk["severity_suggested"] == "CRITICAL"
        assert risk["complaint_category"] == "Contamination"
        assert risk["requires_quarantine"] is True


@pytest.mark.asyncio
async def test_low_impact_label_risk_assessment():
    """Test 3: Verify LOW severity risk assessment for minor cosmetic label issue."""
    mock_risk = RiskAssessmentOutput(
        severity_suggested=RiskSeverity.LOW,
        complaint_category="Packaging Defect",
        suggested_next_action="Perform standard packaging inspection review",
        risk_details="Minor cosmetic label positioning issue without impact on drug product contents.",
        requires_quarantine=False,
    )

    state: AgentState = {
        "current_complaint": {
            "product_name": "Paracetamol Tablets",
            "defect_type": "Cosmetic Label Misalignment",
            "complaint_description": "Customer reported minor issue with external label appearance; product contents unaffected.",
        }
    }

    with patch(
        "app.ai.nodes.risk_assessment.groq_service.generate_structured",
        new_callable=AsyncMock,
        return_value=mock_risk,
    ):
        res = await risk_assessment_node(state)
        risk = res["risk_assessment"]

        assert risk["severity_suggested"] == "LOW"
        assert risk["requires_quarantine"] is False


@pytest.mark.asyncio
async def test_missing_data_risk_assessment():
    """Test 4: Verify risk node executes with partial complaint details without hallucinating missing fields."""
    mock_risk = RiskAssessmentOutput(
        severity_suggested=RiskSeverity.MEDIUM,
        complaint_category="Product Defect",
        suggested_next_action="Request batch number and retain sample for testing",
        risk_details="Damaged tablets indicate potential physical defect, but missing batch and quantity details limit scope.",
        requires_quarantine=False,
    )

    state: AgentState = {
        "current_complaint": {
            "product_name": "Product X",
            "defect_type": "Damaged Tablets",
            "complaint_description": "Customer reported damaged tablets.",
        }
    }

    with patch(
        "app.ai.nodes.risk_assessment.groq_service.generate_structured",
        new_callable=AsyncMock,
        return_value=mock_risk,
    ):
        res = await risk_assessment_node(state)
        assert res["risk_assessment"]["severity_suggested"] == "MEDIUM"


@pytest.mark.asyncio
async def test_no_fake_fallback_on_groq_failure():
    """Test 5 & 6: Verify Groq failure returns None and NEVER fakes a LOW/MEDIUM fallback severity."""
    state: AgentState = {
        "current_complaint": {
            "product_name": "Amoxicillin Capsules",
            "defect_type": "Discoloration",
        }
    }

    with patch(
        "app.ai.nodes.risk_assessment.groq_service.generate_structured",
        new_callable=AsyncMock,
        side_effect=LLMServiceError("Groq service unreachable"),
    ):
        res = await risk_assessment_node(state)
        # MUST return None, NOT fake severity = LOW / MEDIUM
        assert res["risk_assessment"] is None


@pytest.mark.asyncio
async def test_full_graph_risk_assessment_execution():
    """Test 7: Verify full LangGraph flow (LOG_COMPLAINT -> Log Complaint -> Risk Assessment -> Response Synthesis)."""
    mock_extracted = AsyncMock()
    mock_extracted.customer_name = "Apollo Pharmacy"
    mock_extracted.complaint_source = "Pharmacy"
    mock_extracted.product_name = "Amoxicillin Capsules"
    mock_extracted.strength_grade = "500 mg"
    mock_extracted.batch_number = "AMX240602"
    mock_extracted.affected_quantity = "12 capsules"
    mock_extracted.manufacturing_date = "March 2026"
    mock_extracted.expiry_date = "February 2028"
    mock_extracted.complaint_category = "Product Defect"
    mock_extracted.defect_type = "Discoloration"
    mock_extracted.complaint_description = "Apollo Pharmacy reported 12 discolored capsules."
    mock_extracted.model_dump.return_value = {
        "customer_name": "Apollo Pharmacy",
        "product_name": "Amoxicillin Capsules",
        "batch_number": "AMX240602",
        "defect_type": "Discoloration",
    }

    mock_risk = RiskAssessmentOutput(
        severity_suggested=RiskSeverity.HIGH,
        complaint_category="Product Defect",
        suggested_next_action="Route to QA Investigation",
        risk_details="Potential discolored capsules.",
        requires_quarantine=True,
    )

    initial_state: AgentState = {
        "messages": [
            {
                "role": "user",
                "content": "Apollo Pharmacy reported discolored capsules in Amoxicillin Capsules 500 mg.",
            }
        ]
    }

    with patch(
        "app.ai.nodes.classifier.groq_service.generate_structured",
        new_callable=AsyncMock,
        return_value=AsyncMock(intent=Intent.LOG_COMPLAINT),
    ), patch(
        "app.ai.nodes.log_complaint.groq_service.generate_structured",
        new_callable=AsyncMock,
        return_value=mock_extracted,
    ), patch(
        "app.ai.nodes.risk_assessment.groq_service.generate_structured",
        new_callable=AsyncMock,
        return_value=mock_risk,
    ):
        final_state = await compiled_graph.ainvoke(initial_state)

        assert final_state["intent"] == Intent.LOG_COMPLAINT
        assert final_state["risk_assessment"] is not None
        assert final_state["risk_assessment"]["severity_suggested"] == "HIGH"
        assert "risk assessment" in final_state["response_message"].lower()


@pytest.mark.asyncio
async def test_edit_route_risk_compatibility():
    """Test 8: Verify EDIT_COMPLAINT routing preserves compatibility with risk assessment node."""
    initial_state: AgentState = {
        "messages": [{"role": "user", "content": "Sorry, batch number is BMX240602."}],
        "current_complaint": {"product_name": "Amoxicillin Capsules", "batch_number": "AMX240602"},
    }

    mock_risk = RiskAssessmentOutput(
        severity_suggested=RiskSeverity.MEDIUM,
        complaint_category="Product Defect",
        suggested_next_action="Update batch record and review",
        risk_details="Updated batch information evaluated.",
        requires_quarantine=False,
    )

    with patch(
        "app.ai.nodes.classifier.groq_service.generate_structured",
        new_callable=AsyncMock,
        return_value=AsyncMock(intent=Intent.EDIT_COMPLAINT),
    ), patch(
        "app.ai.nodes.risk_assessment.groq_service.generate_structured",
        new_callable=AsyncMock,
        return_value=mock_risk,
    ):
        final_state = await compiled_graph.ainvoke(initial_state)

        assert final_state["intent"] == Intent.EDIT_COMPLAINT
        assert final_state["risk_assessment"] is not None
