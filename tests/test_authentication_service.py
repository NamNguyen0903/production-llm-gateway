from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.core.security import digest_api_key
from app.db.models.api_key import ApiKey
from app.services.authentication_service import (
    AuthenticationService,
    InvalidApiKeyError,
)

TEST_SECRET = "a" * 64
TEST_KEY = "gw_" + "b" * 64
NOW = datetime(2026, 1, 1, tzinfo=UTC)


class FakeApiKeyRepository:
    def __init__(self, record: ApiKey | None) -> None:
        self.record = record
        self.calls = 0

    async def get_by_digest(self, key_digest: str) -> ApiKey | None:
        self.calls += 1

        if self.record is not None and self.record.key_digest == key_digest:
            return self.record

        return None


def make_record(
    *,
    status: str = "active",
    expires_at: datetime | None = None,
) -> ApiKey:
    return ApiKey(
        id=uuid4(),
        name="test-client",
        key_prefix=TEST_KEY[:12],
        key_digest=digest_api_key(TEST_KEY, secret=TEST_SECRET),
        status=status,
        rate_limit_rpm=30,
        expires_at=expires_at,
    )


@pytest.mark.asyncio
async def test_active_key_authenticates() -> None:
    record = make_record()
    repository = FakeApiKeyRepository(record)
    service = AuthenticationService(repository, hmac_secret=TEST_SECRET)

    result = await service.authenticate(TEST_KEY, now=NOW)

    assert result.id == record.id
    assert result.name == "test-client"
    assert result.rate_limit_rpm == 30


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "expires_at"),
    [
        ("revoked", None),
        ("active", NOW - timedelta(seconds=1)),
        ("active", NOW),
    ],
)
async def test_revoked_or_expired_key_is_rejected(
    status: str,
    expires_at: datetime | None,
) -> None:
    repository = FakeApiKeyRepository(
        make_record(status=status, expires_at=expires_at),
    )
    service = AuthenticationService(repository, hmac_secret=TEST_SECRET)

    with pytest.raises(InvalidApiKeyError):
        await service.authenticate(TEST_KEY, now=NOW)


@pytest.mark.asyncio
async def test_future_expiry_is_accepted() -> None:
    repository = FakeApiKeyRepository(
        make_record(expires_at=NOW + timedelta(seconds=1)),
    )
    service = AuthenticationService(repository, hmac_secret=TEST_SECRET)

    await service.authenticate(TEST_KEY, now=NOW)


@pytest.mark.asyncio
async def test_unknown_key_is_rejected() -> None:
    repository = FakeApiKeyRepository(None)
    service = AuthenticationService(repository, hmac_secret=TEST_SECRET)

    with pytest.raises(InvalidApiKeyError):
        await service.authenticate(TEST_KEY, now=NOW)


@pytest.mark.asyncio
async def test_invalid_format_does_not_query_database() -> None:
    repository = FakeApiKeyRepository(None)
    service = AuthenticationService(repository, hmac_secret=TEST_SECRET)

    with pytest.raises(InvalidApiKeyError):
        await service.authenticate("invalid", now=NOW)

    assert repository.calls == 0
