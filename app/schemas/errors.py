from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """Machine-readable information about an API error."""

    code: str
    message: str
    request_id: str
    retryable: bool = False
    details: list[dict[str, object]] | None = None


class ErrorResponse(BaseModel):
    """Standard error envelope returned by the gateway."""

    error: ErrorDetail
