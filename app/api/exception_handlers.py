import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette import status
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppError
from app.schemas.errors import ErrorDetail, ErrorResponse


logger = logging.getLogger(__name__)

REQUEST_ID_HEADER = "X-Request-ID"


def get_request_id(request: Request) -> str:
    """Return the trusted internal request ID when available."""

    request_id = getattr(request.state, "request_id", None)

    if isinstance(request_id, str):
        return request_id

    return "req_unknown"


def create_error_response(
    *,
    request_id: str,
    status_code: int,
    code: str,
    message: str,
    retryable: bool = False,
    details: list[dict[str, object]] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    """Create a response using the gateway error contract."""

    response_headers = dict(headers or {})
    response_headers[REQUEST_ID_HEADER] = request_id

    payload = ErrorResponse(
        error=ErrorDetail(
            code=code,
            message=message,
            request_id=request_id,
            retryable=retryable,
            details=details,
        )
    )

    return JSONResponse(
        status_code=status_code,
        content=payload.model_dump(mode="json"),
        headers=response_headers,
    )


async def handle_app_error(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle an expected application error."""

    if not isinstance(exc, AppError):
        raise TypeError("Expected AppError.")

    return create_error_response(
        request_id=get_request_id(request),
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
        retryable=exc.retryable,
        details=exc.details,
    )


async def handle_validation_error(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Convert Pydantic/FastAPI validation errors into a safe response."""

    if not isinstance(exc, RequestValidationError):
        raise TypeError("Expected RequestValidationError.")

    details: list[dict[str, object]] = []

    for error in exc.errors():
        details.append(
            {
                "type": str(error.get("type", "validation_error")),
                "location": [str(part) for part in error.get("loc", ())],
                "message": str(error.get("msg", "Invalid request value.")),
            }
        )

    return create_error_response(
        request_id=get_request_id(request),
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        code="VALIDATION_ERROR",
        message="The request contains invalid data.",
        retryable=False,
        details=details,
    )


async def handle_http_error(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Normalize framework-generated HTTP errors."""

    if not isinstance(exc, StarletteHTTPException):
        raise TypeError("Expected StarletteHTTPException.")

    if exc.status_code == status.HTTP_404_NOT_FOUND:
        code = "NOT_FOUND"
        message = "The requested resource was not found."
        retryable = False
    elif exc.status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
        code = "METHOD_NOT_ALLOWED"
        message = "The HTTP method is not allowed for this endpoint."
        retryable = False
    else:
        code = "HTTP_ERROR"
        message = "The request could not be completed."
        retryable = False

    return create_error_response(
        request_id=get_request_id(request),
        status_code=exc.status_code,
        code=code,
        message=message,
        retryable=retryable,
        headers=dict(exc.headers or {}),
    )


async def handle_unexpected_error(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Hide unexpected implementation details from API clients."""

    request_id = get_request_id(request)

    logger.error(
        "Unhandled application exception request_id=%s",
        request_id,
        exc_info=(type(exc), exc, exc.__traceback__),
    )

    return create_error_response(
        request_id=request_id,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="INTERNAL_ERROR",
        message="An unexpected internal error occurred.",
        retryable=True,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register the gateway exception handlers."""

    app.add_exception_handler(AppError, handle_app_error)
    app.add_exception_handler(
        RequestValidationError,
        handle_validation_error,
    )
    app.add_exception_handler(
        StarletteHTTPException,
        handle_http_error,
    )
    app.add_exception_handler(
        Exception,
        handle_unexpected_error,
    )
