import asyncio
import logging
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.db.session import get_db_session
from app.repositories.api_key_repository import ApiKeyRepository
from app.services.authentication_service import (
    AuthenticatedApiKey,
    AuthenticationService,
    InvalidApiKeyError,
)

logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer(
    auto_error=False,
    scheme_name="GatewayApiKey",
)

AUTH_DATABASE_TIMEOUT_SECONDS = 3.0


def authentication_error() -> AppError:
    return AppError(
        code="INVALID_API_KEY",
        message="Missing or invalid API key.",
        status_code=401,
        retryable=False,
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_authenticated_api_key(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AuthenticatedApiKey:
    if credentials is None:
        raise authentication_error()

    settings = get_settings()

    if settings.api_key_hmac_secret is None:
        logger.error("API_KEY_HMAC_SECRET is not configured.")
        raise AppError(
            code="AUTHENTICATION_UNAVAILABLE",
            message="Authentication service is temporarily unavailable.",
            status_code=503,
            retryable=True,
        )

    service = AuthenticationService(
        ApiKeyRepository(session),
        hmac_secret=settings.api_key_hmac_secret.get_secret_value(),
    )

    try:
        async with asyncio.timeout(AUTH_DATABASE_TIMEOUT_SECONDS):
            return await service.authenticate(credentials.credentials)
    except InvalidApiKeyError:
        raise authentication_error() from None
    except (SQLAlchemyError, OSError, TimeoutError) as exc:
        logger.warning(
            "API key authentication dependency unavailable: %s",
            type(exc).__name__,
        )
        raise AppError(
            code="AUTHENTICATION_UNAVAILABLE",
            message="Authentication service is temporarily unavailable.",
            status_code=503,
            retryable=True,
        ) from None
