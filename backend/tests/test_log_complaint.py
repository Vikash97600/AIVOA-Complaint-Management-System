import pytest
from unittest.mock import AsyncMock, patch
from app.ai.nodes.log_complaint import log_complaint_node
from app.ai.prompts.log_complaint import ExtractedComplaintData
from app.ai.state import AgentState, Intent


@pytest.mark.asyncio
async def test_apollo_pharmacy_log_complaint():
    """Test 1: Verify full extraction for Apollo Pharmacy complaint example."""
    mock_extracted = ExtractedComplaintData(
        customer_name="Apollo Pharmacy",
        complaint_source="Pharmacy",
        product_name="Amoxicillin Capsules",
        strength_grade="500 mg",
        batch_number="AMX240602",
        affected_quantity="12 capsules",
        manufacturing_date="March 2026",
        expiry_date="February 2028",
        complaint_category="Product Defect",
        defect_type="Discoloration",
        complaint_description="Apollo Pharmacy reported 12 discolored capsules in Amoxicillin Capsules 500 mg."
    )

    state: AgentState = {
        "messages": [
            {
                "role": "user",
                "content": (
                    "Apollo Pharmacy reported discolored capsules in Amoxicillin Capsules 500 mg. "
                    "Batch AMX240602, 12 capsules, manufacturing March 2026, expiry February 2028."
                ),
            }
        ]
    }

    with patch(
        "app.ai.nodes.log_complaint.groq_service.generate_structured",
        new_callable=AsyncMock,
        return_value=mock_extracted,
    ):
        res = await log_complaint_node(state)
        current = res["current_complaint"]

        assert current["customer_name"] == "Apollo Pharmacy"
        assert current["complaint_source"] == "Pharmacy"
        assert current["product_name"] == "Amoxicillin Capsules"
        assert current["strength_grade"] == "500 mg"
        assert current["batch_number"] == "AMX240602"
        assert current["affected_quantity"] == "12 capsules"
        assert current["manufacturing_date"] == "March 2026"
        assert current["expiry_date"] == "February 2028"
        assert "customer_name" in res["updated_fields"]
        assert "batch_number" in res["updated_fields"]


@pytest.mark.asyncio
async def test_missing_information_extraction():
    """Test 2: Verify missing fields return None without hallucination."""
    mock_extracted = ExtractedComplaintData(
        product_name="Product X",
        defect_type="Damaged Tablets",
        complaint_description="Customer reported damaged tablets in Product X."
    )

    state: AgentState = {
        "messages": [{"role": "user", "content": "Customer reported damaged tablets in Product X."}]
    }

    with patch(
        "app.ai.nodes.log_complaint.groq_service.generate_structured",
        new_callable=AsyncMock,
        return_value=mock_extracted,
    ):
        res = await log_complaint_node(state)
        current = res["current_complaint"]

        assert current["product_name"] == "Product X"
        assert current["batch_number"] is None
        assert current["manufacturing_date"] is None
        assert current["expiry_date"] is None
        assert current["affected_quantity"] is None


@pytest.mark.asyncio
async def test_batch_and_quantity_extraction():
    """Test 3: Verify exact batch number and unit quantity preservation."""
    mock_extracted = ExtractedComplaintData(
        batch_number="BMX240602",
        affected_quantity="48 capsules"
    )

    state: AgentState = {
        "messages": [
            {
                "role": "user",
                "content": "Please log a complaint for batch BMX240602. Affected quantity is 48 capsules.",
            }
        ]
    }

    with patch(
        "app.ai.nodes.log_complaint.groq_service.generate_structured",
        new_callable=AsyncMock,
        return_value=mock_extracted,
    ):
        res = await log_complaint_node(state)
        current = res["current_complaint"]

        assert current["batch_number"] == "BMX240602"
        assert current["affected_quantity"] == "48 capsules"
        assert current["customer_name"] is None


@pytest.mark.asyncio
async def test_partial_date_preservation():
    """Test 4: Verify partial dates are preserved as strings without inventing day numbers."""
    mock_extracted = ExtractedComplaintData(
        manufacturing_date="March 2026",
        expiry_date="February 2028"
    )

    state: AgentState = {
        "messages": [
            {
                "role": "user",
                "content": "Product was manufactured in March 2026 and expires in February 2028.",
            }
        ]
    }

    with patch(
        "app.ai.nodes.log_complaint.groq_service.generate_structured",
        new_callable=AsyncMock,
        return_value=mock_extracted,
    ):
        res = await log_complaint_node(state)
        current = res["current_complaint"]

        assert current["manufacturing_date"] == "March 2026"
        assert current["expiry_date"] == "February 2028"
        assert current["manufacturing_date"] != "2026-03-01"


@pytest.mark.asyncio
async def test_no_hallucination_guarantee():
    """Test 5: Verify strict no-hallucination constraint on unmentioned fields."""
    mock_extracted = ExtractedComplaintData(
        customer_name="ABC Pharmacy",
        defect_type="Cracked Tablets"
    )

    state: AgentState = {
        "messages": [{"role": "user", "content": "ABC Pharmacy reported cracked tablets."}]
    }

    with patch(
        "app.ai.nodes.log_complaint.groq_service.generate_structured",
        new_callable=AsyncMock,
        return_value=mock_extracted,
    ):
        res = await log_complaint_node(state)
        current = res["current_complaint"]

        assert current["customer_name"] == "ABC Pharmacy"
        assert current["batch_number"] is None
        assert current["affected_quantity"] is None
        assert current["manufacturing_facility"] is None
