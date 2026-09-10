class AIVOAException(Exception):
    """Base exception class for AIVOA application."""
    pass

class LLMBaseError(AIVOAException):
    """Base exception for LLM operations."""
    pass

class LLMConfigurationError(LLMBaseError):
    """Raised when LLM service is improperly configured (e.g. missing API key)."""
    pass

class LLMAuthenticationError(LLMBaseError):
    """Raised when authentication with LLM provider fails."""
    pass

class LLMRateLimitError(LLMBaseError):
    """Raised when LLM API rate limit is exceeded."""
    pass

class LLMTimeoutError(LLMBaseError):
    """Raised when an LLM request times out."""
    pass

class LLMServiceError(LLMBaseError):
    """Raised when generic LLM service execution fails."""
    pass

class StructuredOutputError(LLMBaseError):
    """Raised when LLM output fails to parse into the requested structured schema."""
    pass
