from fastapi import Request, status
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger("dealflow360.exceptions")


class DealFlowException(Exception):
    """Base exception for all domain business rule violations."""
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST, details: dict = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class UnauthorizedException(DealFlowException):
    def __init__(self, message: str = "Authentication credentials were invalid or missing"):
        super().__init__(message=message, status_code=status.HTTP_401_UNAUTHORIZED)


class ForbiddenException(DealFlowException):
    def __init__(self, message: str = "You do not have permission to perform this action"):
        super().__init__(message=message, status_code=status.HTTP_403_FORBIDDEN)


class NotFoundException(DealFlowException):
    def __init__(self, message: str = "Requested resource was not found"):
        super().__init__(message=message, status_code=status.HTTP_404_NOT_FOUND)


class ConflictException(DealFlowException):
    def __init__(self, message: str = "A resource with the specified identifier already exists"):
        super().__init__(message=message, status_code=status.HTTP_409_CONFLICT)


class BusinessRuleViolationException(DealFlowException):
    def __init__(self, message: str, details: dict = None):
        super().__init__(message=message, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, details=details)


async def dealflow_exception_handler(request: Request, exc: DealFlowException) -> JSONResponse:
    """Centralized exception handler for custom domain exceptions."""
    logger.warning(f"Business Exception [{exc.status_code}] on {request.url.path}: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.message,
                "status_code": exc.status_code,
                "details": exc.details
            }
        }
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Fallback exception handler that logs internal server errors without leaking stack traces."""
    logger.error(f"Unhandled Exception on {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "message": "An internal server error occurred.",
                "status_code": 500
            }
        }
    )
