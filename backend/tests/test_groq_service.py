import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pydantic import BaseModel
import groq

from app.core.config import settings
from app.core.ai_exceptions import (
    LLMConfigurationError,
    LLMAuthenticationError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMServiceError,
    StructuredOutputError,
)
from app.services.groq_service import GroqService, groq_service


class DummySchema(BaseModel):
    intent: str


@pytest.mark.asyncio
async def test_groq_missing_api_key():
    """Test 1: Verify missing API key raises LLMConfigurationError on generation."""
    service = GroqService()
    with patch.object(settings, "GROQ_API_KEY", None):
        with pytest.raises(LLMConfigurationError) as exc_info:
            await service.generate([{"role": "user", "content": "Hello"}])
        assert "GROQ_API_KEY is not configured" in str(exc_info.value)


def test_groq_model_default_configuration():
    """Test 2: Verify default configured model is gemma2-9b-it."""
    assert settings.GROQ_MODEL == "gemma2-9b-it"


@pytest.mark.asyncio
async def test_groq_successful_text_generation():
    """Test 3a: Verify successful text completion using mocked AsyncGroq."""
    service = GroqService()
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Response from Gemma"
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch.object(settings, "GROQ_API_KEY", "mock_key"):
        with patch.object(service, "get_client", return_value=mock_client):
            res = await service.generate([{"role": "user", "content": "Test prompt"}])
            assert res == "Response from Gemma"
            mock_client.chat.completions.create.assert_called_once()


@pytest.mark.asyncio
async def test_groq_successful_structured_generation():
    """Test 3b: Verify structured output generation and Pydantic validation."""
    service = GroqService()
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = '{"intent": "LOG_COMPLAINT"}'
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch.object(settings, "GROQ_API_KEY", "mock_key"):
        with patch.object(service, "get_client", return_value=mock_client):
            parsed: DummySchema = await service.generate_structured(
                messages=[{"role": "user", "content": "Log a complaint"}],
                response_model=DummySchema,
            )
            assert parsed.intent == "LOG_COMPLAINT"


@pytest.mark.asyncio
async def test_groq_authentication_failure():
    """Test 4a: Verify AuthenticationError maps to LLMAuthenticationError."""
    service = GroqService()
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(
        side_effect=groq.AuthenticationError(
            message="Invalid Key",
            response=MagicMock(status_code=401),
            body=None,
        )
    )

    with patch.object(settings, "GROQ_API_KEY", "invalid_key"):
        with patch.object(service, "get_client", return_value=mock_client):
            with pytest.raises(LLMAuthenticationError):
                await service.generate([{"role": "user", "content": "Test"}])


@pytest.mark.asyncio
async def test_groq_rate_limit_failure():
    """Test 4b: Verify RateLimitError maps to LLMRateLimitError."""
    service = GroqService()
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(
        side_effect=groq.RateLimitError(
            message="Rate limit reached",
            response=MagicMock(status_code=429),
            body=None,
        )
    )

    with patch.object(settings, "GROQ_API_KEY", "mock_key"):
        with patch.object(service, "get_client", return_value=mock_client):
            with pytest.raises(LLMRateLimitError):
                await service.generate([{"role": "user", "content": "Test"}])


@pytest.mark.asyncio
async def test_groq_timeout_failure():
    """Test 4c: Verify APITimeoutError maps to LLMTimeoutError after retries."""
    service = GroqService()
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(
        side_effect=groq.APITimeoutError(request=MagicMock())
    )

    with patch.object(settings, "GROQ_API_KEY", "mock_key"):
        with patch.object(service, "get_client", return_value=mock_client):
            with pytest.raises(LLMTimeoutError):
                await service.generate([{"role": "user", "content": "Test"}])
