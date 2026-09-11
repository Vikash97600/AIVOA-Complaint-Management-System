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

class InvalidDocumentTypeError(AIVOAException):
    def __init__(self, message: str = "Unsupported document type. Please upload a PDF, EML, or TXT file."):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST
        )

class DocumentOversizedError(AIVOAException):
    def __init__(self, message: str = "The uploaded file exceeds the maximum allowed size."):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST
        )

class DocumentExtractionError(AIVOAException):
    def __init__(self, message: str = "No readable text could be extracted from the document."):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST
        )

class ComplaintAlreadyCommittedError(AIVOAException):
    def __init__(self, complaint_id: str = ""):
        msg = f"Complaint '{complaint_id}' has already been committed to the QMS Ledger and cannot be edited." if complaint_id else "This complaint has already been committed to the QMS Ledger and cannot be edited."
        super().__init__(
            message=msg,
            status_code=status.HTTP_409_CONFLICT
        )

class ComplaintNotReadyForCommitError(AIVOAException):
    def __init__(self, message: str = "Complaint is not in a valid state to be committed."):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST
        )

class RiskAssessmentMissingError(AIVOAException):
    def __init__(self, message: str = "Complaint cannot be committed because the risk assessment is unavailable."):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST
        )

class QMSCommitError(AIVOAException):
    def __init__(self, message: str = "Failed to commit complaint to QMS Ledger."):
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
