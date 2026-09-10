import asyncio
import json
import time
import re
from typing import List, Dict, Any, Optional, Type, TypeVar
from pydantic import BaseModel
import groq

from app.core.config import settings
from app.core.logging_config import logger
from app.core.ai_exceptions import (
    LLMConfigurationError,
    LLMAuthenticationError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMServiceError,
    StructuredOutputError,
)

T = TypeVar("T", bound=BaseModel)


class GroqService:
    """
    Dedicated LLM Service encapsulating all communication with Groq API.
    Provides standard text generation and schema-validated structured output.
    """

    def __init__(self):
        self._client: Optional[groq.AsyncGroq] = None

    def get_client(self) -> groq.AsyncGroq:
        """
        Lazily initializes and returns the AsyncGroq client.
        Raises LLMConfigurationError if GROQ_API_KEY is missing or unconfigured.
        """
        api_key = settings.GROQ_API_KEY
        if not api_key or not api_key.strip() or api_key == "your_groq_api_key_here":
            raise LLMConfigurationError(
                "GROQ_API_KEY is not configured in environment settings."
            )

        if self._client is None:
            self._client = groq.AsyncGroq(
                api_key=api_key,
                timeout=settings.GROQ_TIMEOUT,
            )
        return self._client

    async def generate(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: Optional[float] = None,
        response_format: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
        operation: str = "llm_generate",
    ) -> str:
        """
        Executes a completion request against Groq API with robust error handling and retries.
        """
        client = self.get_client()
        target_model = model or settings.GROQ_MODEL
        target_temp = (
            temperature if temperature is not None else settings.GROQ_TEMPERATURE
        )
        target_max_tokens = max_tokens or settings.GROQ_MAX_TOKENS
        target_timeout = timeout or settings.GROQ_TIMEOUT

        start_time = time.perf_counter()
        logger.info(
            f"AI request starting | operation={operation} | model={target_model} | request_id={request_id}"
        )

        max_attempts = 2

        for attempt in range(1, max_attempts + 1):
            try:
                response = await client.chat.completions.create(
                    model=target_model,
                    messages=messages,
                    temperature=target_temp,
                    max_tokens=target_max_tokens,
                    timeout=target_timeout,
                    response_format=response_format,
                )

                duration_ms = (time.perf_counter() - start_time) * 1000
                logger.info(
                    f"AI request completed | operation={operation} | model={target_model} | "
                    f"duration_ms={duration_ms:.2f} | request_id={request_id}"
                )

                content = response.choices[0].message.content
                if content is None:
                    return ""
                return content.strip()

            except groq.AuthenticationError as e:
                logger.error(f"Groq authentication failure for request_id={request_id}: {e}")
                raise LLMAuthenticationError(
                    "Groq authentication failed. Please verify GROQ_API_KEY."
                ) from e

            except groq.RateLimitError as e:
                logger.error(f"Groq rate limit hit for request_id={request_id}: {e}")
                raise LLMRateLimitError("Groq API rate limit exceeded.") from e

            except (groq.APITimeoutError, groq.APIConnectionError) as e:
                logger.warning(
                    f"Groq transient network error (attempt {attempt}/{max_attempts}) for request_id={request_id}: {e}"
                )
                if attempt == max_attempts:
                    raise LLMTimeoutError("Groq request timed out.") from e
                await asyncio.sleep(0.5)

            except groq.APIError as e:
                status = getattr(e, "status_code", 500)
                if status and status >= 500 and attempt < max_attempts:
                    logger.warning(
                        f"Groq server error {status} (attempt {attempt}/{max_attempts}). Retrying..."
                    )
                    await asyncio.sleep(0.5)
                    continue

                logger.error(f"Groq API error for request_id={request_id}: {e}")
                error_msg = getattr(e, "message", str(e))
                raise LLMServiceError(f"Groq request failed: {error_msg}") from e

            except Exception as e:
                logger.error(f"Unexpected error during Groq invocation for request_id={request_id}: {e}")
                raise LLMServiceError(f"Groq execution failed: {str(e)}") from e

        raise LLMServiceError("Groq request failed after retries.")

    async def generate_structured(
        self,
        messages: List[Dict[str, str]],
        response_model: Type[T],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: Optional[float] = None,
        request_id: Optional[str] = None,
        operation: str = "llm_generate_structured",
    ) -> T:
        """
        Generates structured output from Groq and validates it against the provided Pydantic model.
        """
        raw_response = await self.generate(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
            response_format={"type": "json_object"},
            request_id=request_id,
            operation=operation,
        )

        clean_json_str = self._extract_json_str(raw_response)

        try:
            return response_model.model_validate_json(clean_json_str)
        except Exception as e:
            logger.error(
                f"Failed to parse LLM response into schema {response_model.__name__} for request_id={request_id}: {e}. "
                f"Raw content: '{raw_response[:200]}...'"
            )
            raise StructuredOutputError(
                f"Failed to validate response against schema {response_model.__name__}: {str(e)}"
            ) from e

    def _extract_json_str(self, text: str) -> str:
        """Safely extracts JSON payload from text response."""
        text = text.strip()
        if "```" in text:
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
            if match:
                return match.group(1).strip()

        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and start < end:
            return text[start : end + 1].strip()

        return text


# Create reusable global service instance
groq_service = GroqService()
