import pytest
from unittest.mock import AsyncMock, patch
from app.ai.nodes.edit_complaint import edit_complaint_node
from app.ai.prompts.edit_complaint import ComplaintEditOutput
from app.ai.state import AgentState, Intent
from app.ai.graph import compiled_graph
from app.ai.prompts.risk_assessment import RiskAssessmentOutput
from app.database.models import RiskSeverity


@pytest.mark.asyncio
async def test_apollo_pharmacy_edit_primary_scenario():
    """Test 1: Verify primary edit scenario (batch number and affected quantity updated, rest unchanged)."""
    initial_complaint = {
        "customer_name": "Apollo Pharmacy",
        "complaint_source": "Pharmacy",
        "product_name": "Amoxicillin Capsules",
        "strength_grade": "500 mg",
        "batch_number": "AMX240602",
        "affected_quantity": "12 capsules",
        "manufacturing_date": "March 2026",
        "expiry_date": "February 2028",
        "defect_type": "Discoloration",
        "complaint_category": "Product Defect",
        "complaint_description": "Apollo Pharmacy reported 12 discolored capsules.",
    }

    state: AgentState = {
        "complaint_id": "test-uuid-1234",
        "current_complaint": initial_complaint,
        "messages": [
            {
                "role": "user",
                "content": "Sorry, batch number is BMX240602, affected quantity is 48 capsules.",
            }
        ],
    }

    mock_edit_output = ComplaintEditOutput(
        updated_fields=["batch_number", "affected_quantity"],
        changes={"batch_number": "BMX240602", "affected_quantity": "48 capsules"},
    )

    with patch(
        "app.ai.nodes.edit_complaint.groq_service.generate_structured",
        new_callable=AsyncMock,
        return_value=mock_edit_output,
    ):
        res = await edit_complaint_node(state)
        merged = res["current_complaint"]

        assert res["updated_fields"] == ["batch_number", "affected_quantity"]
        assert merged["batch_number"] == "BMX240602"
        assert merged["affected_quantity"] == "48 capsules"
        assert merged["customer_name"] == "Apollo Pharmacy"
        assert merged["product_name"] == "Amoxicillin Capsules"
        assert merged["strength_grade"] == "500 mg"
        assert merged["manufacturing_date"] == "March 2026"
        assert merged["expiry_date"] == "February 2028"


@pytest.mark.asyncio
async def test_single_field_quantity_edit():
    """Test 2: Verify single field edit updates ONLY affected_quantity."""
    initial_complaint = {"product_name": "Amoxicillin Capsules", "batch_number": "AMX240602", "affected_quantity": "12 capsules"}
    state: AgentState = {
        "complaint_id": "test-uuid-1234",
        "current_complaint": initial_complaint,
        "messages": [{"role": "user", "content": "Please change the affected quantity to 50 capsules."}],
    }

    mock_edit_output = ComplaintEditOutput(
        updated_fields=["affected_quantity"],
        changes={"affected_quantity": "50 capsules"},
    )

    with patch(
        "app.ai.nodes.edit_complaint.groq_service.generate_structured",
        new_callable=AsyncMock,
        return_value=mock_edit_output,
    ):
        res = await edit_complaint_node(state)
        assert res["updated_fields"] == ["affected_quantity"]
        assert res["current_complaint"]["affected_quantity"] == "50 capsules"
        assert res["current_complaint"]["batch_number"] == "AMX240602"


@pytest.mark.asyncio
async def test_explicit_field_clear():
    """Test 7: Verify explicit field clearing sets field to None without affecting other attributes."""
    initial_complaint = {"product_name": "Amoxicillin Capsules", "expiry_date": "February 2028"}
    state: AgentState = {
        "complaint_id": "test-uuid-1234",
        "current_complaint": initial_complaint,
        "messages": [{"role": "user", "content": "Remove the expiry date because it is not available."}],
    }

    mock_edit_output = ComplaintEditOutput(
        updated_fields=["expiry_date"],
        changes={"expiry_date": None},
    )

    with patch(
        "app.ai.nodes.edit_complaint.groq_service.generate_structured",
        new_callable=AsyncMock,
        return_value=mock_edit_output,
    ):
        res = await edit_complaint_node(state)
        assert res["updated_fields"] == ["expiry_date"]
        assert res["current_complaint"]["expiry_date"] is None
        assert res["current_complaint"]["product_name"] == "Amoxicillin Capsules"


@pytest.mark.asyncio
async def test_ambiguous_edit_no_guessing():
    """Test 8: Verify ambiguous edit request makes no changes and asks for clarification."""
    initial_complaint = {"product_name": "Amoxicillin Capsules", "batch_number": "AMX240602"}
    state: AgentState = {
        "complaint_id": "test-uuid-1234",
        "current_complaint": initial_complaint,
        "messages": [{"role": "user", "content": "Please correct the complaint."}],
    }

    mock_edit_output = ComplaintEditOutput(updated_fields=[], changes={})

    with patch(
        "app.ai.nodes.edit_complaint.groq_service.generate_structured",
        new_callable=AsyncMock,
        return_value=mock_edit_output,
    ):
        res = await edit_complaint_node(state)
        assert res["updated_fields"] == []
        assert res["current_complaint"]["batch_number"] == "AMX240602"
        assert "specify" in res["response_message"].lower()


@pytest.mark.asyncio
async def test_missing_complaint_id_handling():
    """Test 10: Verify missing complaint_id does not create a new complaint or modify state."""
    state: AgentState = {
        "complaint_id": None,
        "current_complaint": None,
        "messages": [{"role": "user", "content": "Change the batch to BMX240602."}],
    }

    res = await edit_complaint_node(state)
    assert res["updated_fields"] == []
    assert "select or log a complaint" in res["response_message"].lower()


@pytest.mark.asyncio
async def test_full_graph_edit_and_risk_reevaluation():
    """Test 11 & 14: Verify full LangGraph flow (EDIT_COMPLAINT -> Edit Node -> Risk Node -> Response Synthesis)."""
    initial_complaint = {
        "customer_name": "Apollo Pharmacy",
        "product_name": "Amoxicillin Capsules",
        "batch_number": "AMX240602",
        "affected_quantity": "12 capsules",
    }

    mock_edit_output = ComplaintEditOutput(
        updated_fields=["batch_number", "affected_quantity"],
        changes={"batch_number": "BMX240602", "affected_quantity": "48 capsules"},
    )

    mock_risk_output = RiskAssessmentOutput(
        severity_suggested=RiskSeverity.HIGH,
        complaint_category="Product Defect",
        suggested_next_action="Route to QA Investigation for updated batch BMX240602",
        risk_details="Re-evaluated risk for 48 capsules of batch BMX240602.",
        requires_quarantine=True,
    )

    initial_state: AgentState = {
        "complaint_id": "test-uuid-9999",
        "current_complaint": initial_complaint,
        "messages": [{"role": "user", "content": "Sorry, batch number is BMX240602, affected quantity is 48 capsules."}],
    }

    with patch(
        "app.ai.nodes.classifier.groq_service.generate_structured",
        new_callable=AsyncMock,
        return_value=AsyncMock(intent=Intent.EDIT_COMPLAINT),
    ), patch(
        "app.ai.nodes.edit_complaint.groq_service.generate_structured",
        new_callable=AsyncMock,
        return_value=mock_edit_output,
    ), patch(
        "app.ai.nodes.risk_assessment.groq_service.generate_structured",
        new_callable=AsyncMock,
        return_value=mock_risk_output,
    ):
        final_state = await compiled_graph.ainvoke(initial_state)

        assert final_state["intent"] == Intent.EDIT_COMPLAINT
        assert final_state["current_complaint"]["batch_number"] == "BMX240602"
        assert final_state["current_complaint"]["affected_quantity"] == "48 capsules"
        assert final_state["current_complaint"]["customer_name"] == "Apollo Pharmacy"
        assert final_state["risk_assessment"]["severity_suggested"] == "HIGH"
        assert "risk assessment" in final_state["response_message"].lower()
