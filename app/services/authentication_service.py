from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from app.core.security import digest_api_key, is_valid_api_key_format
from app.db.models.api_key import ApiKey


class InvalidApiKeyError(Exception):
    """The supplied API key cannot authenticate the caller."""


class ApiKeyReader(Protocol):
    async def get_by_digest(self, key_digest: str) -> ApiKey | None: ...


@dataclass(frozen=True)
class AuthenticatedApiKey:
    id: UUID
    name: str
    rate_limit_rpm: int


class AuthenticationService:
    def __init__(
        self,
        repository: ApiKeyReader,
        *,
        hmac_secret: str,
    ) -> None:
        if len(hmac_secret.encode("utf-8")) < 32:
            raise ValueError("API key HMAC secret is too short.")

        self._repository = repository
        self._hmac_secret = hmac_secret

    async def authenticate(
        self,
        raw_key: str,
        *,
        now: datetime | None = None,
    ) -> AuthenticatedApiKey:
        if not is_valid_api_key_format(raw_key):
            raise InvalidApiKeyError("Invalid API key.")

        key_digest = digest_api_key(
            raw_key,
            secret=self._hmac_secret,
        )

        api_key = await self._repository.get_by_digest(key_digest)

        if api_key is None or api_key.status != "active":
            raise InvalidApiKeyError("Invalid API key.")

        current_time = now if now is not None else datetime.now(UTC)

        if api_key.expires_at is not None and api_key.expires_at <= current_time:
            raise InvalidApiKeyError("Invalid API key.")

        return AuthenticatedApiKey(
            id=api_key.id,
            name=api_key.name,
            rate_limit_rpm=api_key.rate_limit_rpm,
        )
