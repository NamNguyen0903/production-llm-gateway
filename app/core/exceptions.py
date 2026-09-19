class AppError(Exception):
    """Base exception for expected application errors."""

    def __init__(
        self,
        *,
        status_code: int,
        code: str,
        message: str,
        retryable: bool = False,
        details: list[dict[str, object]] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)

        self.status_code = status_code
        self.code = code
        self.headers = headers or {}
        self.message = message
        self.retryable = retryable
        self.details = details
