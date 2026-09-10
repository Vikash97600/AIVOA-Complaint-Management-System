from fastapi import Request, status
from fastapi.responses import JSONResponse
from app.core.logging_config import logger

class AIVOAException(Exception):
    """Base exception for AIVOA application."""
    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.message = message
        self.status_code = status_code
        super().__init__(message)

class ComplaintNotFoundError(AIVOAException):
    def __init__(self, complaint_id: str):
        super().__init__(
            message=f"Complaint with ID '{complaint_id}' not found",
            status_code=status.HTTP_404_NOT_FOUND
        )

class DatabaseOperationError(AIVOAException):
    def __init__(self, message: str = "A database operation error occurred"):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

async def aivoa_exception_handler(request: Request, exc: AIVOAException) -> JSONResponse:
    logger.warning(f"AIVOA Exception [{exc.status_code}] on {request.url.path}: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )

async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Unhandled server error on {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred"}
    )
