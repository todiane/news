from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict, Any, Optional
from pydantic import BaseModel
import logging
import traceback

logger = logging.getLogger(__name__)

class ErrorDetail(BaseModel):
    """Standardized error response model."""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid input data",
                "details": {
                    "field": "email",
                    "error": "Invalid email format"
                }
            }
        }

class APIErrorHandler:
    """Centralized API error handling."""
    
    def __init__(self):
        self.error_mappings = {
            RequestValidationError: self._handle_validation_error,
            SQLAlchemyError: self._handle_database_error,
            ValueError: self._handle_value_error,
            KeyError: self._handle_key_error,
            Exception: self._handle_generic_error
        }

    async def handle_exception(
        self,
        request: Request,
        exc: Exception
    ) -> JSONResponse:
        """Main exception handler that routes to specific handlers."""
        handler = self.error_mappings.get(type(exc), self._handle_generic_error)
        return await handler(request, exc)

    async def _handle_validation_error(
        self,
        request: Request,
        exc: RequestValidationError
    ) -> JSONResponse:
        """Handle Pydantic validation errors."""
        errors = []
        for error in exc.errors():
            errors.append({
                "field": error["loc"][-1],
                "type": error["type"],
                "message": error["msg"]
            })
            
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorDetail(
                code="VALIDATION_ERROR",
                message="Invalid input data",
                details={"errors": errors}
            ).dict()
        )

    async def _handle_database_error(
        self,
        request: Request,
        exc: SQLAlchemyError
    ) -> JSONResponse:
        """Handle database-related errors."""
        logger.error(f"Database error: {str(exc)}")
        logger.debug(traceback.format_exc())
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorDetail(
                code="DATABASE_ERROR",
                message="Database operation failed",
                details={"error": str(exc)} if request.app.debug else None
            ).dict()
        )

    async def _handle_value_error(
        self,
        request: Request,
        exc: ValueError
    ) -> JSONResponse:
        """Handle ValueError exceptions."""
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorDetail(
                code="VALUE_ERROR",
                message=str(exc)
            ).dict()
        )

    async def _handle_key_error(
        self,
        request: Request,
        exc: KeyError
    ) -> JSONResponse:
        """Handle KeyError exceptions."""
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorDetail(
                code="KEY_ERROR",
                message=f"Missing required key: {str(exc)}"
            ).dict()
        )

    async def _handle_generic_error(
        self,
        request: Request,
        exc: Exception
    ) -> JSONResponse:
        """Handle any unhandled exceptions."""
        logger.error(f"Unhandled error: {str(exc)}")
        logger.debug(traceback.format_exc())
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorDetail(
                code="INTERNAL_ERROR",
                message="An unexpected error occurred"
            ).dict()
        )

    async def _handle_feed_error(
        self,
        request: Request,
        exc: Exception
    ) -> JSONResponse:
        """Handle feed-specific errors."""
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorDetail(
                code="FEED_ERROR",
                message=str(exc),
                details={"url": getattr(exc, "url", None)}
            ).dict()
        )

error_handler = APIErrorHandler()
