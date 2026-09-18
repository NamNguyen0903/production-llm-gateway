from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Assign a trusted internal request ID to every HTTP request."""

    def __init__(
        self,
        app: ASGIApp,
        header_name: str = "X-Request-ID",
    ) -> None:
        super().__init__(app)
        self.header_name = header_name

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        request_id = f"req_{uuid4().hex}"
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers[self.header_name] = request_id

        return response
