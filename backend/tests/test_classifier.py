import pytest
from unittest.mock import AsyncMock, patch
from app.ai.nodes.classifier import classifier_node
from app.ai.prompts.classifier import ClassifierOutput
from app.ai.state import AgentState, Intent
from app.core.ai_exceptions import LLMConfigurationError


@pytest.mark.asyncio
async def test_classifier_log_complaint():
    """Test 1: Classify LOG_COMPLAINT intent with mocked LLM output."""
    mock_output = ClassifierOutput(intent=Intent.LOG_COMPLAINT)
    state: AgentState = {
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
        return_value=mock_output,
    ):
        res = await classifier_node(state)
        assert res["intent"] == Intent.LOG_COMPLAINT


@pytest.mark.asyncio
async def test_classifier_edit_complaint():
    """Test 2: Classify EDIT_COMPLAINT intent with mocked LLM output."""
    mock_output = ClassifierOutput(intent=Intent.EDIT_COMPLAINT)
    state: AgentState = {
        "messages": [
            {
                "role": "user",
                "content": "Sorry, the batch number is BMX240602 and affected quantity is 48 capsules.",
            }
        ]
    }

    with patch(
        "app.ai.nodes.classifier.groq_service.generate_structured",
        new_callable=AsyncMock,
        return_value=mock_output,
    ):
        res = await classifier_node(state)
        assert res["intent"] == Intent.EDIT_COMPLAINT


@pytest.mark.asyncio
async def test_classifier_document_extraction():
    """Test 3: Classify DOCUMENT_EXTRACTION intent with mocked LLM output."""
    mock_output = ClassifierOutput(intent=Intent.DOCUMENT_EXTRACTION)
    state: AgentState = {
        "messages": [
            {
                "role": "user",
                "content": "Extract the complaint details from this uploaded complaint PDF.",
            }
        ]
    }

    with patch(
        "app.ai.nodes.classifier.groq_service.generate_structured",
        new_callable=AsyncMock,
        return_value=mock_output,
    ):
        res = await classifier_node(state)
        assert res["intent"] == Intent.DOCUMENT_EXTRACTION


@pytest.mark.asyncio
async def test_classifier_unknown_intent():
    """Test 4: Classify UNKNOWN intent with mocked LLM output."""
    mock_output = ClassifierOutput(intent=Intent.UNKNOWN)
    state: AgentState = {
        "messages": [{"role": "user", "content": "Hello, what can you do?"}]
    }

    with patch(
        "app.ai.nodes.classifier.groq_service.generate_structured",
        new_callable=AsyncMock,
        return_value=mock_output,
    ):
        res = await classifier_node(state)
        assert res["intent"] == Intent.UNKNOWN


@pytest.mark.asyncio
async def test_classifier_fallback_on_unconfigured_groq():
    """Test 5: Verify fallback keyword classifier works when Groq raises an exception."""
    state: AgentState = {
        "messages": [
            {
                "role": "user",
                "content": "Apollo Pharmacy reported discolored capsules",
            }
        ]
    }

    with patch(
        "app.ai.nodes.classifier.groq_service.generate_structured",
        new_callable=AsyncMock,
        side_effect=LLMConfigurationError("Missing API Key"),
    ):
        res = await classifier_node(state)
        assert res["intent"] == Intent.LOG_COMPLAINT
